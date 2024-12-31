
import contextlib
import fcntl
from functools import wraps
import gzip
import os
import pickle
from urllib.parse import parse_qs, urlencode
from werkzeug.wrappers import Response
from aisikl.exceptions import LoggedOutError


def get_sessid_from_cookie(request):
    return request.votr_cookie_value.get('sessid')


def check_sessid(sessid):
    for ch in sessid:
        if ch not in '0123456789abcdef_':
            raise ValueError('Invalid sessid')


def open_log_file(request, sessid):
    check_sessid(sessid)
    filename = request.app.var / 'logs' / (sessid + '.gz')
    return gzip.open(filename, 'at', encoding='utf8')


def create(request, sessid, session):
    check_sessid(sessid)
    with open(request.app.var / 'sessions' / sessid, 'xb') as f:
        pickle.dump(session, f, pickle.HIGHEST_PROTOCOL)

    return sessid


def delete(request, sessid=None):
    if not sessid: sessid = get_sessid_from_cookie(request)
    if not sessid: return
    check_sessid(sessid)
    try:
        os.unlink(request.app.var / 'sessions' / sessid)
        return True
    except FileNotFoundError:
        return False


@contextlib.contextmanager
def lock(app, sessid):
    """Acquires a named mutex identified by ``sessid``, waiting if another
    process/thread is already holding it. If a process dies, its held locks are
    automatically released. Locks are per user."""
    # This is implemented with file locks, specifically BSD locks (flock). See
    # https://gavv.github.io/articles/file-locks/ for a comparison. lockf and
    # POSIX locks (fcntl) behave badly on close (threads can unlock each other).
    #
    # Instead of locking the session file or the log file, we use dedicated
    # lock files, because it can be significant to delete the session or log
    # file while the sessid is still locked.
    #
    # The lock file is deleted when we're done (to clean up after ourselves). We
    # use the algorithm from https://stackoverflow.com/q/17708885 to avoid race
    # conditions when one thread deletes the file but another thread already has
    # it open and is trying to lock it.
    check_sessid(sessid)
    lock_base = f'{app.settings.instance_id}.{os.getuid()}.{sessid}'
    lock_path = app.var / 'locks' / lock_base
    while True:
        f = open(lock_path, 'ab')
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)

            # Lock acquired, but is it still the same file? Compare inodes.
            my_inode = os.fstat(f.fileno()).st_ino
            try:
                inode_on_disk = os.stat(lock_path).st_ino
            except FileNotFoundError:
                inode_on_disk = None
            if my_inode != inode_on_disk:
                # File was already deleted. Close it and try to open it again.
                continue

            try:
                yield
            finally:
                # Whether the body succeeded or not, unlink and close the file.
                os.unlink(lock_path)

            return
        finally:
            f.close()


@contextlib.contextmanager
def transaction(request, sessid=None):
    if not sessid: sessid = get_sessid_from_cookie(request)
    if not sessid: raise LoggedOutError('Session cookie not found')
    check_sessid(sessid)

    with lock(request.app, sessid):
        try:
            f = open(request.app.var / 'sessions' / sessid, 'r+b')
        except FileNotFoundError as e:
            raise LoggedOutError('Votr session does not exist') from e

        with f:
            session = pickle.load(f)

            if (credentials := session.get('credentials')):
                if (username := credentials.get('username')):
                    request.environ['votr.log_user'] = username

            yield session

            # Use pickle.dumps instead of pickle.dump, so that if it fails, the
            # session file is not truncated.
            new_content = pickle.dumps(session, pickle.HIGHEST_PROTOCOL)

            f.seek(0)
            f.truncate(0)
            f.write(new_content)


@contextlib.contextmanager
def logged_transaction(request, sessid=None):
    if not sessid: sessid = get_sessid_from_cookie(request)

    with transaction(request, sessid) as session:
        with open_log_file(request, sessid) as log_file:
            client = session.get('client')
            if client: client.context.logger.log_file = log_file
            yield session
