
import contextlib
import fcntl
import gzip
import os
import pickle
from aisikl.exceptions import LoggedOutError


def _session_cookie_name(request):
    prefix = '__Host-' if request.app.settings.secure_session_cookie else ''
    return prefix + request.app.settings.instance_id + '_sessid'


def get_session_cookie(request):
    return request.cookies.get(_session_cookie_name(request))


def set_session_cookie(request, response, sessid):
    secure = request.app.settings.secure_session_cookie
    if sessid:
        response.set_cookie(_session_cookie_name(request), sessid,
            path='/', secure=secure, httponly=True, samesite='Lax')
    else:
        response.delete_cookie(_session_cookie_name(request),
            path='/', secure=secure, httponly=True, samesite='Lax')
    return response


def check_sessid(sessid):
    for ch in sessid:
        if ch not in '0123456789abcdef_':
            raise ValueError('Invalid sessid')


def get_filename(request, sessid, *, logs=False):
    check_sessid(sessid)
    return request.app.var_path('logs' if logs else 'sessions', sessid)


def open_log_file(request, sessid):
    filename = get_filename(request, sessid, logs=True) + '.gz'
    return gzip.open(filename, 'at', encoding='utf8')


def create(request, sessid, session):
    with open(get_filename(request, sessid), 'xb') as f:
        pickle.dump(session, f, pickle.HIGHEST_PROTOCOL)

    return sessid


def delete(request, sessid=None):
    if not sessid: sessid = get_session_cookie(request)
    if not sessid: return
    try:
        os.unlink(get_filename(request, sessid))
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
    lock_path = os.path.join(
        app.settings.lock_path,
        '{}.{}.{}'.format(app.settings.instance_id, os.getuid(), sessid))
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
    if not sessid: sessid = get_session_cookie(request)
    if not sessid: raise LoggedOutError('Session cookie not found')

    with lock(request.app, sessid):
        try:
            f = open(get_filename(request, sessid), 'r+b')
        except FileNotFoundError as e:
            raise LoggedOutError('Votr session does not exist') from e

        with f:
            session = pickle.load(f)

            yield session

            # Use pickle.dumps instead of pickle.dump, so that if it fails, the
            # session file is not truncated.
            new_content = pickle.dumps(session, pickle.HIGHEST_PROTOCOL)

            f.seek(0)
            f.truncate(0)
            f.write(new_content)


@contextlib.contextmanager
def logged_transaction(request, sessid=None):
    if not sessid: sessid = get_session_cookie(request)

    with transaction(request, sessid) as session:
        with open_log_file(request, sessid) as log_file:
            client = session.get('client')
            if client: client.context.logger.log_file = log_file
            yield session
