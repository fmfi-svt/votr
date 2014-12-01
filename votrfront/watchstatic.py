
import os
import subprocess
import sys
import threading
import time


votrfront_path = os.path.dirname(__file__) or '.'
watch_paths = ['buildstatic.sh', 'js', 'css']
watch_extensions = ['.sh', '.js', '.scss']


def build():
    command = ['./buildstatic.sh']
    if hasattr(sys, 'real_prefix'):
        command.append('--env=' + sys.prefix)
    returncode = subprocess.call(command, cwd=votrfront_path)
    print(' * buildstatic.sh failed' if returncode else
          ' * buildstatic.sh ended successfully', file=sys.stderr)


def walk(root):
    if os.path.isfile(root):
        yield root
    if os.path.isdir(root):
        for dirpath, dirnames, filenames in os.walk(root):
            for filename in filenames:
                yield os.path.join(dirpath, filename)


def watch(interval=1):
    last_build = time.time()
    build()

    while True:
        modified_files = []

        for root in watch_paths:
            for filename in walk(os.path.join(votrfront_path, root)):
                if os.path.splitext(filename)[1] not in watch_extensions:
                    continue
                try:
                    mtime = os.stat(filename).st_mtime
                    if mtime > last_build:
                        modified_files.append(filename)
                except OSError:
                    continue

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
