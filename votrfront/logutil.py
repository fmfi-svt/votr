import contextlib
import gzip
import json
import lzma
import os
import re
import sqlite3
import subprocess
import sys
import time
import traceback
import trio
from votrfront import sessions
from votrfront.base import var_path


TAG_PREFIX = '%'
PAGER = ['less', '-RS']
BASE_PATTERN = r'"\w+", "[\w ]+ failed'

def classify(line):
    if "failed with Cancelled" in line.content:
        return 'Cancelled'
    if "base.ps.PSException: Nie je connection" in line.content:
        return 'SQLError'
    if "java.sql.SQLException: Connection is not valid" in line.content:
        return 'SQLError'
    if "args=['Nie je connection.'" in line.content:
        return 'SQLError'
    if "args=['Nastala SQL chyba" in line.content:
        return 'SQLError'
    if "failed with ConnectError" in line.content:
        return 'ConnectionError'
    if "failed with HTTPStatusError" in line.content:
        return 'HTTPError'
    if "failed with LoggedOutError" in line.content:
        return 'LoggedOutError'
    if "Login failed with PasswordLoginError" in line.content:
        return 'KnownLoginError'
    if "Login failed with CookieLoginError" in line.content:
        return 'KnownLoginError'
    if ("zapis_plan_vyhladaj" in line.content and
            "AIS did not return all table rows" in line.content):
        return 'open issue121'
    return 'open'


# ----------------------------------------


class Line:
    def __init__(self, sessid, lineno, tags, content, timestamp):
        self.sessid = sessid
        self.lineno = lineno
        self.tags = tags
        self.content = content
        self.timestamp = timestamp


def connect_logdb():
    logdb = sqlite3.connect(var_path('logdb/logdb.sqlite'))
    c = logdb.cursor()
    # sub(\s+) is just to look nicer when you print ".schema".
    c.execute(re.sub(r'\s+', ' ', '''
        CREATE TABLE IF NOT EXISTS lines (
            sessid TEXT,
            lineno INTEGER,
            tags TEXT,
            content TEXT,
            timestamp INTEGER GENERATED ALWAYS AS (JSON_EXTRACT(content, '$[0]')) STORED,
            PRIMARY KEY (sessid, lineno)
        )
    '''))
    c.execute('CREATE INDEX IF NOT EXISTS lines_tags ON lines (tags)')
    c.execute('CREATE INDEX IF NOT EXISTS lines_timestamp ON lines (timestamp)')
    return logdb


def locate(sessid):
    sessid = str(sessid)
    if '/' in sessid:
        options = [sessid]
    else:
        options = [
            var_path('logs', sessid),  # legacy
            var_path('logs', sessid + '.gz'),
            var_path('oldlogs', sessid[0:2], sessid + '.gz'),  # legacy
            var_path('oldlogs', sessid + '.xz'),
            sessid,
        ]
    for option in options:
        if os.path.exists(option):
            return str(option)
    raise ValueError('Log not found: %r' % sessid)


def open_log(filename):
    if str(filename).endswith('.gz'):
        return gzip.open(filename, 'rt', encoding='utf8')
    elif str(filename).endswith('.xz'):
        return lzma.open(filename, 'rt', encoding='utf8')
    else:
        return open(filename, encoding='utf8')


def set_tags(logdb, sessid, lineno, tags_to_add, tags_to_remove):
    c = logdb.cursor()
    c.execute('SELECT tags FROM lines WHERE sessid = ? AND lineno = ?',
        (sessid, lineno))
    old_tags = c.fetchone()[0]
    tags = { t: True for t in old_tags.split() }
    for tag in tags_to_remove:
        tags.pop(tag, None)
    for tag in tags_to_add:
        tags[tag] = True
    c.execute('UPDATE lines SET tags = ? WHERE sessid = ? AND lineno = ? AND tags = ?',
        (' '.join(tags), sessid, lineno, old_tags))


async def process_logfiles(logdb, files):
    c = logdb.cursor()

    errors = []

    for filename in files:
        sessid = os.path.basename(filename).partition('.')[0]
        async with sessions.lock(sessid):
            try:
                with open_log(filename) as f:
                    lineno = 0
                    for line in f:
                        json.loads(line)  # Validate JSON.
                        lineno += 1
                        if re.search(BASE_PATTERN, line):
                            try:
                                c.execute(
                                    'INSERT INTO lines (sessid, lineno, tags, content) VALUES (?, ?, ?, ?)',
                                    (sessid, lineno, 'new', line.strip()))
                            except sqlite3.IntegrityError:
                                pass   # row already present
                    if lineno == 0:
                        raise Exception('Log file is empty')
            except Exception:
                errors.append((filename, sys.exc_info()))

    c.execute("SELECT * FROM lines WHERE tags = 'new'")
    for sessid, lineno, tags, content, timestamp in c:
        line = Line(sessid, lineno, tags, content, timestamp)
        new_tags = classify(line).split()
        if new_tags:
            set_tags(logdb, sessid, lineno, new_tags, ['new'])

    logdb.commit()

    if errors:
        msgs = [f'{len(errors)} errors occurred while processing logs:']
        for filename, exc_info in errors:
            errmsg = ''.join(traceback.format_exception(*exc_info))
            msgs.append(
                f'{filename}:\n' +
                '\n'.join('    ' + line for line in errmsg.split('\n')))
        raise Exception('\n\n'.join(msgs))

@contextlib.contextmanager
def wrap_pager():
    if os.isatty(0) and os.isatty(1):
        sp = subprocess.Popen(PAGER, stdin=subprocess.PIPE, encoding='utf8')
        try:
            yield sp.stdin
        except BrokenPipeError:
            print('Broken pipe', file=sys.stderr)
        sp.stdin.close()
        if sp.wait() != 0:
            raise OSError("Pager return code %s" % sp.returncode)
    else:
        yield sys.stdout


# ----------------------------------------


def cli_tag(*args):
    # Use dict instead of set as it has consistent insertion iteration order in
    # Python 3.7+, unlike set. (https://stackoverflow.com/q/3848091)
    targets = {}
    tags_to_add = {}
    tags_to_remove = {}

    for arg in args:
        if arg.startswith('--'):
            raise ValueError("Long options not supported: %r" % arg)
        if arg.startswith('-') and len(arg) <= 2:
            raise ValueError("Ambiguous short tag: %r" % arg)
        if arg.startswith('+') or arg.startswith('-'):
            name = arg[1:].lstrip(TAG_PREFIX)
            if not name:
                raise ValueError("Empty tag: %r" % arg)
            if ' ' in name:
                raise ValueError("Space in tag name: %r" % arg)
            tags_to = tags_to_add if arg.startswith('+') else tags_to_remove
            tags_to[name] = True
        else:
            targets[arg] = True

    logdb = connect_logdb()

    for target in targets:
        sessid, _, lineno = target.partition(':')
        set_tags(logdb, sessid, int(lineno), tags_to_add, tags_to_remove)

    logdb.commit()


def cli_view(*args):
    color = False
    sessid = None

    it = iter(args)
    for arg in it:
        if arg == '-c' or arg == '--color':
            color = True
        elif arg.startswith('-'):
            raise ValueError('Unknown option: %r' % arg)
        elif sessid is not None:
            raise ValueError('Too many arguments')
        else:
            sessid = arg

    if not sessid:
        raise ValueError('No sessid or filename given')

    filename = locate(sessid)

    with wrap_pager() as out:
        with open_log(filename) as f:
            for line in f:
                timestamp, type, message, data = json.loads(line)
                tm = time.localtime(timestamp)
                separator = "~" * 80
                typestr = "<"+type+">"
                when = '[%4d-%02d-%02d %02d:%02d:%02d = %.7f]' % (
                    tm.tm_year, tm.tm_mon, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec, timestamp)
                if color:
                    print("\033[1;31m%s\033[0m" % separator, file=out)
                    print("\033[33m%s\033[0m \033[32m%s\033[0m \033[1;36m%s\033[0m" % (when, typestr, message), file=out)
                else:
                    print(separator, file=out)
                    print(when, typestr, message, file=out)
                if type == 'http' and isinstance(data, dict) and 'headers' in data:
                    print({ k: v for k, v in data.items() if k != 'headers' and k != 'body' }, file=out)
                    for k, v in data['headers']:
                        print(f'{k}: {v}', file=out)
                    if 'body' in data:
                        print('---', file=out)
                        print(data['body'], file=out)
                else:
                    print(data, file=out)


def cli_path(*sessids):
    for sessid in sessids:
        print(locate(sessid))


def format_base(line):
    tm = time.localtime(line.timestamp)
    when = '%4d-%02d-%02d %02d:%02d:%02d' % (
        tm.tm_year, tm.tm_mon, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec)
    tags = ' '.join(TAG_PREFIX + tag for tag in line.tags.split())
    return (line.sessid, line.lineno, when, tags, line.content)

def format_plain(line):
    return '%s:%-5s %s %-20s %s' % format_base(line)

def format_color(line):
    sessid, lineno, when, tags, content = format_base(line)

    content = re.sub(
        r'( "RPC )(\w+)( failed with )(\w+)(")',
        '\\1\033[1;31m\\2\033[0m\\3\033[1;31m\\4\033[0m\\5', content)
    content = re.sub(
        r'( ")([\w ]+)( failed with )(\w+)(")',
        '\\1\033[1;31m\\2\033[0m\\3\033[1;31m\\4\033[0m\\5', content)

    content = content.replace('\\\\', '\x00').split('\\n')
    if len(content) >= 2: content[-2] = '\033[36m' + content[-2] + '\033[0m'
    content = '\\n'.join(content).replace('\x00', '\\\\')

    return '%s:%-5s \033[1;33m%s\033[0m \033[1;34m%-20s\033[0m %s' % (sessid, lineno, when, tags, content)

def format_sessids(line):
    return line.sessid

def format_linenos(line):
    return '%s:%s' % (line.sessid, line.lineno)

def format_files(line):
    return locate(line.sessid)


def cli_list(*args):
    match = []
    match_not = []
    match_from = None
    match_to = None
    formatter = format_plain

    it = iter(args)
    for arg in it:
        if arg == '-n' or arg == '--not':
            match_not.append(next(it))
        elif arg == '-F' or arg == '--from':
            match_from = int(next(it))
        elif arg == '-T' or arg == '--to':
            match_to = int(next(it))
        elif arg == '-c' or arg == '--color':
            formatter = format_color
        elif arg == '-s' or arg == '--sessids':
            formatter = format_sessids
        elif arg == '-l' or arg == '--linenos':
            formatter = format_linenos
        elif arg == '-f' or arg == '--files':
            formatter = format_files
        elif arg.startswith('-'):
            raise ValueError('Unknown option: %r' % arg)
        else:
            match.append(arg)

    query = 'SELECT * FROM lines WHERE 1'
    params = []

    if match_from is None:
        match_from = 00000000
    else:
        query += " AND timestamp > cast(strftime('%s', ?, '-2 days') as number)"
        params.append('%04d-%02d-%02d' % (match_from // 10000, match_from // 100 % 100, match_from % 100))

    if match_to is None:
        match_to = 99999999
    else:
        query += " AND timestamp < cast(strftime('%s', ?, '+2 days') as number)"
        params.append('%04d-%02d-%02d' % (match_to // 10000, match_to // 100 % 100, match_to % 100))

    # Patterns are regexps which can match anywhere in the formatted line.
    # But simple patterns like '%foo' also have to match the tags column, to
    # keep things fast. Wrap it in '()' if you really want whole line regexp.
    for pattern in match:
        if re.match(r'^T\w+$'.replace('T', re.escape(TAG_PREFIX)), pattern):
            query += ' AND tags LIKE ?'
            params.append('%' + pattern[1:] + '%')

    query += ' ORDER BY timestamp'

    logdb = connect_logdb()
    c = logdb.cursor()
    c.execute(query, params)
    with wrap_pager() as out:
        for sessid, lineno, tags, content, timestamp in c:
            line = Line(sessid, lineno, tags, content, timestamp)
            plain = format_plain(line)
            tm = time.localtime(line.timestamp)
            date = int('%d%02d%02d' % (tm.tm_year, tm.tm_mon, tm.tm_mday))

            if (
                all(re.search(pattern, plain) for pattern in match) and
                all(not re.search(pattern, plain) for pattern in match_not) and
                match_from <= date <= match_to
            ):
                print(formatter(line), file=out)


def cli_process(*files):
    if not files:
        raise ValueError('No files given')
    logdb = connect_logdb()
    trio.run(process_logfiles, logdb, files)


log_commands = {
    'tag': cli_tag,
    'view': cli_view,
    'path': cli_path,
    'list': cli_list,
    'process': cli_process,
}


def cli(*args):
    if not args:
        sys.exit('Missing log subcommand\nTry: ./x --help')
    if args[0] not in log_commands:
        sys.exit('Unknown log subcommand\nTry: ./x --help')
    log_commands[args[0]](*args[1:])


if __name__ == '__main__':
    cli(*sys.argv[1:])
