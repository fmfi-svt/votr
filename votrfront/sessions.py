
import contextlib
import fcntl
import pickle
import os
from werkzeug.contrib.sessions import generate_key


def get_cookie(request):
    return request.cookies.get(request.app.session_name)


def set_cookie(request, sessid, response):
    if sessid:
        response.set_cookie(request.app.session_name, sessid)
    else:
        response.delete_cookie(request.app.session_name)
    return response


def get_filename(request, sessid):
    for ch in sessid:
        if ch not in '0123456789abcdef':
            raise ValueError('Invalid sessid')

    return os.path.join(request.app.settings.session_path, sessid)


def create(request, session):
    sessid = generate_key()

    with open(get_filename(request, sessid), 'xb') as f:
        pickle.dump(session, f, pickle.HIGHEST_PROTOCOL)

    return sessid


def delete(request, sessid=None):
    if not sessid: sessid = get_cookie(request)
    if not sessid: return
    try:
        os.unlink(get_filename(request, sessid))
        return True
    except FileNotFoundError:
        return False


@contextlib.contextmanager
def transaction(request, sessid=None):
    if not sessid: sessid = get_cookie(request)

    with open(get_filename(request, sessid), 'r+b') as f:
        # Use flock instead of fcntl or lockf. flock has sane semantics on
        # close(2), and we don't need fcntl's byte range locks.
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)

        session = pickle.load(f)

        yield session

        # Use pickle.dumps instead of pickle.dump, so that if it fails, the
        # session file is not truncated.
        new_content = pickle.dumps(session, pickle.HIGHEST_PROTOCOL)

        f.seek(0)
        f.truncate(0)
        f.write(new_content)
