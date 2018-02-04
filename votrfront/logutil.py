
import contextlib
import gzip
import io
import json
import os
import re
import sqlite3
import subprocess
import sys
import time


TAG_PREFIX = '%'
PAGER = ['less', '-RS']
BASE_PATTERN = r' "RPC \w+ failed'

def classify(line):
    if "OSError: failed to write data" in line.content:
        return 'OSError'
    if "'Neautorizovaný prístup!', 'Chyba'" in line.content:
        return 'unauthorized'
    if "base.ps.PSException: Nie je connection" in line.content:
        return 'SQLError'
    if "java.sql.SQLException: Connection is not valid" in line.content:
        return 'SQLError'
    if "failed with ConnectionError" in line.content:
        return 'ConnectionError'
    if "failed with SSLError" in line.content:
        return 'ConnectionError'
    if "failed with HTTPError" in line.content:
        return 'HTTPError'
    if "failed with LoggedOutError" in line.content:
        return 'LoggedOutError'
    return 'open'


# ----------------------------------------


class Line:
    def __init__(self, sessid, lineno, tags, content):
        self.sessid = sessid
        self.lineno = lineno
        self.tags = tags
        self.content = content
        self.timestamp, self.type, self.message, self.data = json.loads(content)


def _connect(app):
    if not hasattr(app, 'logutil_conn'):
        app.logutil_conn = sqlite3.connect(app.var_path('logdb/logdb.sqlite'))
        c = app.logutil_conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS lines (
            sessid TEXT,
            lineno INTEGER,
            tags TEXT,
            content TEXT,
            PRIMARY KEY (sessid, lineno)
        )
        ''')
    return app.logutil_conn


def locate(app, sessid):
    options = [
        app.var_path('logs', sessid),
        app.var_path('oldlogs', sessid[0:2], sessid + '.gz'),
        sessid,
    ]
    for option in options:
        if os.path.exists(option):
            return option
    raise ValueError('Log not found: %r' % sessid)


def open_log(filename):
    if filename.endswith('.gz'):
        return gzip.open(filename, 'rt', encoding='utf8')
    else:
        return open(filename, encoding='utf8')


def get_lines(app):
    lines = []
    c = _connect(app).cursor()
    c.execute('SELECT * FROM lines')
    for sessid, lineno, tags, content in c.fetchall():
        lines.append(Line(sessid, lineno, tags, content))
    return sorted(lines, key=lambda l: l.timestamp)


def set_tags(app, sessid, lineno, tags_to_add, tags_to_remove):
    c = _connect(app).cursor()
    c.execute('SELECT tags FROM lines WHERE sessid = ? AND lineno = ?',
        (sessid, lineno))
    old_tags = c.fetchone()[0]
    tags = old_tags.split()
    for tag in tags_to_remove:
        if tag in tags:
            tags.remove(tag)
    for tag in tags_to_add:
        if tag not in tags:
            tags.append(tag)
    c.execute('UPDATE lines SET tags = ? WHERE sessid = ? AND lineno = ? AND tags = ?',
        (' '.join(tags), sessid, lineno, old_tags))


def process_logfiles(app, files):
    c = _connect(app).cursor()

    for filename in files:
        sessid = os.path.basename(filename).partition('.')[0]
        with open_log(filename) as f:
            lineno = 0
            for line in f:
                lineno += 1
                if re.search(BASE_PATTERN, line):
                    try:
                        c.execute('INSERT INTO lines VALUES (?, ?, ?, ?)',
                            (sessid, lineno, 'new', line.strip()))
                    except sqlite3.IntegrityError:
                        pass   # row already present

    for line in get_lines(app):
        if line.tags == 'new':
            new_tags = classify(line).split()
            if new_tags:
                set_tags(app, line.sessid, line.lineno, new_tags, ['new'])

    _connect(app).commit()

@contextlib.contextmanager
def wrap_pager():
    if os.isatty(0) and os.isatty(1):
        buf = io.StringIO()
        yield buf
        sp = subprocess.Popen(PAGER, stdin=subprocess.PIPE)
        sp.communicate(buf.getvalue().encode('utf8'))
    else:
        yield sys.stdout


# ----------------------------------------


def cli_tag(app, *args):
    targets = set()
    tags_to_add = set()
    tags_to_remove = set()

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
            (tags_to_add if arg.startswith('+') else tags_to_remove).add(name)
        else:
            targets.add(arg)

    for target in targets:
        sessid, _, lineno = target.partition(':')
        set_tags(app, sessid, int(lineno), tags_to_add, tags_to_remove)

    _connect(app).commit()


def cli_view(app, sessid):
    filename = locate(app, sessid)

    with wrap_pager() as out:
        with open_log(filename) as f:
            for line in f:
                timestamp, type, message, data = json.loads(line)
                print("-" * 80, file=out)
                print("{"+type+"}", message, file=out)
                print(data, file=out)


def cli_path(app, *sessids):
    for sessid in sessids:
        print(locate(app, sessid))


def format_base(app, line):
    tm = time.localtime(line.timestamp)
    when = '%4d-%02d-%02d %02d:%02d:%02d' % (
        tm.tm_year, tm.tm_mon, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec)
    tags = ' '.join(TAG_PREFIX + tag for tag in line.tags.split())
    return (line.sessid, line.lineno, when, tags, line.content)

def format_plain(app, line):
    return '%s:%-5s %s %-20s %s' % format_base(app, line)

def format_color(app, line):
    sessid, lineno, when, tags, content = format_base(app, line)

    content = re.sub(
        r'( "RPC )(\w+)( failed with )(\w+)(")',
        '\\1\033[1;31m\\2\033[0m\\3\033[1;31m\\4\033[0m\\5', content)

    content = content.replace('\\\\', '\x00').split('\\n')
    if len(content) >= 2: content[-2] = '\033[36m' + content[-2] + '\033[0m'
    content = '\\n'.join(content).replace('\x00', '\\\\')

    return '%s:%-5s \033[1;33m%s\033[0m \033[1;34m%-20s\033[0m %s' % (sessid, lineno, when, tags, content)

def format_sessids(app, line):
    return line.sessid

def format_linenos(app, line):
    return '%s:%s' % (line.sessid, line.lineno)

def format_files(app, line):
    return locate(app, line.sessid)


def cli_list(app, *args):
    match = []
    match_not = []
    match_from = 00000000
    match_to = 99999999
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

    with wrap_pager() as out:
        for line in get_lines(app):
            plain = format_plain(app, line)
            tm = time.localtime(line.timestamp)
            date = int('%d%02d%02d' % (tm.tm_year, tm.tm_mon, tm.tm_mday))

            if (all(re.search(pattern, plain) for pattern in match) and
                all(not re.search(pattern, plain) for pattern in match_not) and
                match_from <= date <= match_to):
                print(formatter(app, line), file=out)


def cli_process(app, *files):
    if not files:
        raise ValueError('No files given')
    process_logfiles(app, files)


log_commands = {
    'tag': cli_tag,
    'view': cli_view,
    'path': cli_path,
    'list': cli_list,
    'process': cli_process,
}


def cli(app, *args):
    if not args or args[0] not in log_commands:
        return app.run_help()
    log_commands[args[0]](app, *args[1:])

cli.help = (
    '  $0 log tag +TAGNAME1 -TAGNAME2 SESSID1:LINENO1 SESSID2:LINENO2 ...\n'
    '  $0 log view SESSID\n'
    '  $0 log view FILENAME\n'
    '  $0 log path SESSID1 SESSID2 ...\n'
    '  $0 log list PATTERN ...\n'
    '    -n, --not PATTERN     do not select lines matching PATTERN\n'
    '    -F, --from YYYYMMDD   match only lines logged since the given date\n'
    '    -T, --to YYYYMMDD     match only lines logged until the given date\n'
    '    -c, --color           print colored output\n'
    '    -s, --sessids         print list of matching sessids\n'
    '    -l, --linenos         print list of matching sessid:linenos\n'
    '    -f, --files           print list of matching filenames'
)


commands = {
    'log': cli,
}
