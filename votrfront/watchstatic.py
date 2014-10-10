
import os
import subprocess
import sys
import threading
import time


votrfront_path = os.path.dirname(__file__) or '.'
src_path = votrfront_path + '/static/src/'


def build():
    returncode = subprocess.call(['./buildstatic.sh'], cwd=votrfront_path)
    print(' * buildstatic.sh failed' if returncode else
          ' * buildstatic.sh ended successfully', file=sys.stderr)


def watch(interval=1):
    last_build = time.time()
    build()

    while True:
        modified_files = []

        for dirpath, dirnames, filenames in os.walk(src_path):
            for filename in filenames:
                full_path = os.path.join(dirpath, filename)
                try:
                    mtime = os.stat(full_path).st_mtime
                except OSError:
                    continue

                if mtime > last_build:
                    modified_files.append(full_path)

        if modified_files:
            print(' * Detected change in {}, rebuilding static'.format(
                repr(modified_files)[1:-1]), file=sys.stderr)
            last_build = time.time()
            build()

        time.sleep(interval)


def watch_in_background():
    t = threading.Thread(target=watch)
    t.daemon = True
    t.start()
    return t


if __name__ == '__main__':
    watch()
