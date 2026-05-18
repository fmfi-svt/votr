
import contextlib
import fcntl
import gzip
import os
import pickle
import trio
from aisikl.exceptions import LoggedOutError
from votrfront.base import var_path


def get_sessid_from_cookie(request):
    return request.state['votr_cookie_value'].get('sessid')


def check_sessid(sessid):
    for ch in sessid:
        if ch not in '0123456789abcdef_':
            raise LoggedOutError('Invalid sessid')


def open_log_file(sessid):
    check_sessid(sessid)
    filename = var_path('logs', sessid + '.gz')
    return gzip.open(filename, 'at', encoding='utf8')


def create(request, sessid, session):
    check_sessid(sessid)
    with var_path('sessions', sessid).open('xb') as f:
        pickle.dump(session, f, pickle.HIGHEST_PROTOCOL)

    return sessid


def delete(request, sessid=None):
    if not sessid: sessid = get_sessid_from_cookie(request)
    if not sessid: return
    check_sessid(sessid)
    try:
        var_path('sessions', sessid).unlink()
        return True
    except FileNotFoundError:
        return False


@contextlib.asynccontextmanager
async def lock(sessid):
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
    lock_path = var_path('locks', sessid)
    while True:
        f = open(lock_path, 'ab')
        try:
            await trio.to_thread.run_sync(
                fcntl.flock, f.fileno(), fcntl.LOCK_EX,
                abandon_on_cancel=True)

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


@contextlib.asynccontextmanager
async def transaction(request, sessid=None):
    if not sessid: sessid = get_sessid_from_cookie(request)
    if not sessid: raise LoggedOutError('Session cookie not found')
    check_sessid(sessid)

    async with lock(sessid):
        try:
            f = var_path('sessions', sessid).open('r+b')
        except FileNotFoundError as e:
            raise LoggedOutError('Votr session does not exist') from e

        with f:
            session = pickle.load(f)

            if (credentials := session.get('credentials')):
                if (username := credentials.get('username')):
                    request.state['votr_log_user'] = username

            try:
                yield session
            finally:
                # Use pickle.dumps instead of pickle.dump, so that if it fails,
                # the session file is not truncated.
                new_content = pickle.dumps(session, pickle.HIGHEST_PROTOCOL)

                f.seek(0)
                f.truncate(0)
                f.write(new_content)


@contextlib.asynccontextmanager
async def logged_transaction(request, sessid=None):
    if not sessid: sessid = get_sessid_from_cookie(request)

    async with transaction(request, sessid) as session:
        with open_log_file(sessid) as log_file:
            client = session.get('client')
            if client: client.context.logger.log_file = log_file
            yield session
