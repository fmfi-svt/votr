
import datetime
import gzip
import json
import lzma
import os
import shutil
import tarfile
import time
from . import logutil
from . import sessions


def create_archive(app, prefix):
    wip = app.var / 'logarchive' / 'wip.tar.xz'
    sources = sorted((app.var / 'oldlogs').glob(prefix + '*.xz'))
    dest = app.var / 'logarchive' / (prefix + '.tar.xz')

    if os.path.exists(wip):
        os.unlink(wip)

    if not os.path.exists(dest):
        with tarfile.open(wip, 'w:xz', preset=9) as tar:
            for source in sources:
                with lzma.open(source) as f:
                    last = None
                    for line in f: last = line
                    if last is None: raise Exception(source)
                    if not last.endswith(b']\n'): raise Exception(source)
                    mtime = json.loads(last.decode('utf8'))[0]
                    size = f.tell()
                    f.seek(0)

                    tarinfo = tarfile.TarInfo('logs/' + source.name[:-3])
                    tarinfo.size = size
                    tarinfo.mtime = mtime
                    tar.addfile(tarinfo, fileobj=f)

        os.rename(wip, dest)

    with tarfile.open(dest, 'r') as tar:
        for entry in tar:
            sessid = entry.name.rpartition('/')[2]
            path = app.var / 'oldlogs' / (sessid + '.xz')
            if os.path.exists(path):
                os.unlink(path)

    remains = list((app.var / 'oldlogs').glob(prefix + '*.xz'))
    if remains:
        raise Exception('Remaining files: %r' % remains)


def cron(app):
    now = time.time()

    for path in (app.var / 'sessions').iterdir():
        with sessions.lock(app, path.name):
            if not os.path.exists(path): continue  # Logged out just now?
            mtime = os.path.getmtime(path)
            if now - mtime > app.settings.session_max_age:
                os.unlink(path)

    logutil.process_logfiles(
        app, [str(path) for path in (app.var / 'logs').iterdir()])

    for path in (app.var / 'logs').glob('*.gz'):
        sessid = path.name.partition('.')[0]
        with sessions.lock(app, sessid):
            mtime = os.path.getmtime(path)
            if not (now - mtime > app.settings.session_max_age): continue
            if os.path.exists(app.var / 'sessions' / sessid): continue

            newpath = app.var / 'oldlogs' / (sessid + '.xz')

            with gzip.open(path) as src:
                with lzma.open(newpath, 'w', preset=9) as dest:
                    shutil.copyfileobj(src, dest)
            os.unlink(path)

    prefixes = set(path.name[0:6] for path in (app.var / 'oldlogs').glob('*.xz'))

    prefixes.discard(datetime.datetime.utcfromtimestamp(now).strftime('%Y%m'))

    for path in (app.var / 'logs').iterdir():
        prefixes.discard(path.name[0:6])
    for path in (app.var / 'sessions').iterdir():
        prefixes.discard(path.name[0:6])
    for prefix in prefixes:
        create_archive(app, prefix)

cron.help = '  $0 cron'


commands = {
    'cron': cron,
}
