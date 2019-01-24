
import datetime
import gzip
import json
import lzma
import os
import shutil
import subprocess
import tarfile
import time
from . import logutil


def create_archive(app, prefix):
    wip = app.var_path('logarchive', 'wip.tar.xz')
    sources = [filename for filename in os.listdir(app.var_path('oldlogs'))
               if filename.startswith(prefix) and filename.endswith('.xz')]
    sources.sort()
    dest = app.var_path('logarchive', prefix + '.tar.xz')

    if os.path.exists(wip):
        os.unlink(wip)

    if not os.path.exists(dest):
        with tarfile.open(wip, 'w:xz', preset=9) as tar:
            for source in sources:
                with lzma.open(app.var_path('oldlogs', source)) as f:
                    last = None
                    for line in f: last = line
                    if last is None: raise Exception(source)
                    if not last.endswith(b']\n'): raise Exception(source)
                    mtime = json.loads(last.decode('utf8'))[0]
                    size = f.tell()
                    f.seek(0)

                    tarinfo = tarfile.TarInfo('logs/' + source[:-3])
                    tarinfo.size = size
                    tarinfo.mtime = mtime
                    tar.addfile(tarinfo, fileobj=f)

        os.rename(wip, dest)

    with tarfile.open(dest, 'r') as tar:
        for entry in tar:
            sessid = entry.name.rpartition('/')[2]
            path = app.var_path('oldlogs', sessid + '.xz')
            if os.path.exists(path):
                os.unlink(path)

    remains = [filename for filename in os.listdir(app.var_path('oldlogs'))
               if filename.startswith(prefix) and filename.endswith('.xz')]
    if remains:
        raise Exception('Remaining files: %r' % remains)


def cron(app):
    logutil.process_logfiles(
        app, [app.var_path('logs', filename)
              for filename in os.listdir(app.var_path('logs'))])

    now = time.time()

    for sessid in os.listdir(app.var_path('sessions')):
        path = app.var_path('sessions', sessid)
        mtime = os.path.getmtime(path)
        if now - mtime > app.settings.session_max_age:
            os.unlink(path)

    for filename in os.listdir(app.var_path('logs')):
        if not filename.endswith('.gz'): continue
        path = app.var_path('logs', filename)
        sessid = filename.partition('.')[0]
        mtime = os.path.getmtime(path)
        if not (now - mtime > app.settings.session_max_age): continue
        if os.path.exists(app.var_path('sessions', sessid)): continue

        newpath = app.var_path('oldlogs', sessid + '.xz')

        with gzip.open(path) as src:
            with lzma.open(newpath, 'w', preset=9) as dest:
                shutil.copyfileobj(src, dest)
        os.unlink(path)

    this_month = datetime.datetime.utcfromtimestamp(now).strftime('%Y%m')
    prefixes = set(
        filename[0:6] for filename in os.listdir(app.var_path('oldlogs'))
        if filename.endswith('.xz') and not filename.startswith(this_month))

    for filename in os.listdir(app.var_path('logs')):
        prefixes.discard(filename[0:6])
    for filename in os.listdir(app.var_path('sessions')):
        prefixes.discard(filename[0:6])
    for prefix in prefixes:
        create_archive(app, prefix)

cron.help = '  $0 cron'


commands = {
    'cron': cron,
}
