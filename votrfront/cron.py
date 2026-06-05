from datetime import datetime, UTC
import gzip
import json
import lzma
import shutil
import tarfile
import time
from votrfront import logutil
from votrfront import sessions
from votrfront.base import var_path


def create_archive(prefix):
    wip = var_path('logarchive', 'wip.tar.xz')
    sources = sorted(var_path('oldlogs').glob(prefix + '*.xz'))
    dest = var_path('logarchive', prefix + '.tar.xz')

    wip.unlink(missing_ok=True)

    if not dest.exists():
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

        wip.rename(dest)

    with tarfile.open(dest, 'r') as tar:
        for entry in tar:
            sessid = entry.name.rpartition('/')[2]
            var_path('oldlogs', sessid + '.xz').unlink(missing_ok=True)

    remains = sorted(var_path('oldlogs').glob(prefix + '*.xz'))
    if remains:
        raise Exception(f'Remaining files: {remains!r}')


def cron(app):
    settings = app.settings
    now = time.time()

    for path in var_path('sessions').iterdir():
        with sessions.lock(path.name):
            if not path.exists(): continue  # Logged out just now?
            mtime = path.stat().st_mtime
            if now - mtime > settings.session_max_age:
                path.unlink()

    logutil.process_logfiles(
        logutil.connect_logdb(),
        [str(path) for path in var_path('logs').iterdir()],
    )

    for path in var_path('logs').glob('*.gz'):
        sessid = path.name.partition('.')[0]
        with sessions.lock(sessid):
            mtime = path.stat().st_mtime
            if not (now - mtime > settings.session_max_age): continue
            if var_path('sessions', sessid).exists(): continue

            newpath = var_path('oldlogs', sessid + '.xz')

            with gzip.open(path) as src:
                with lzma.open(newpath, 'w', preset=9) as dest:
                    shutil.copyfileobj(src, dest)
            path.unlink()

    prefixes = set(path.name[0:6] for path in var_path('oldlogs').glob('*.xz'))

    prefixes.discard(datetime.fromtimestamp(now, UTC).strftime('%Y%m'))

    for path in var_path('logs').iterdir():
        prefixes.discard(path.name[0:6])
    for path in var_path('sessions').iterdir():
        prefixes.discard(path.name[0:6])
    for prefix in sorted(prefixes):
        create_archive(prefix)


commands = {
    'cron': cron,
}
