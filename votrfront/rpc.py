
import json
import traceback
from werkzeug.routing import Rule
from aisikl.exceptions import LoggedOutError
from . import sessions


def encode_result(thing):
    if isinstance(thing, tuple) and hasattr(thing, '_asdict'):
        thing = thing._asdict()

    if isinstance(thing, (list, tuple)):
        return [encode_result(item) for item in thing]
    if isinstance(thing, dict):
        return { key: encode_result(value) for key, value in thing.items() }
    return thing


def rpc_handle_call(request, session):
    name = request.args['name']
    args = json.loads(request.get_data(as_text=True))
    log = session['client'].context.log

    try:
        log('rpc', 'RPC {} started'.format(name), args)
        method = getattr(session['client'], name)
        result = encode_result(method(*args))
    except Exception as e:
        log('rpc', 'RPC {} failed with {}'.format(name, type(e).__name__),
            traceback.format_exc())
        raise
    log('rpc', 'RPC {} finished'.format(name), result)
    return result


def rpc_handle_sessions(request, send_json):
    if not sessions.get_cookie(request):
        raise LoggedOutError('Session cookie not found')

    with sessions.logged_transaction(request) as session:
        if 'client' not in session:
            # Can happen if /logout and /rpc happen in parallel. If /rpc has
            # opened the session file and is waiting for flock, then it will
            # keep the open file even when /logout unlinks it.
            raise LoggedOutError('Votr session is currently logging out')
        if request.headers.get('X-CSRF-Token') != session['csrf_token']:
            raise ValueError('Bad X-CSRF-Token value')

        def send_log(timestamp, type, message, data):
            send_json({ 'log': type, 'message': message, 'time': timestamp })

        session['client'].context.send_log = send_log
        result = rpc_handle_call(request, session)
        del session['client'].context.send_log

    return result


def rpc_handle_exceptions(request, send_json):
    try:
        result = rpc_handle_sessions(request, send_json)
    except Exception:
        send_json({ 'error': traceback.format_exc() })
    else:
        send_json({ 'result': result })


def rpc_handle_partials(request):
    def wsgi_response(environ, start_response):
        write = start_response('200 OK', [
            ('Content-Type', 'text/plain'),
            # Prevent https://code.google.com/p/chromium/issues/detail?id=2016
            # (onprogress only happening after the client receives 1024 bytes)
            # See also: ShouldSniffContent(), kMaxBytesToSniff
            ('X-Content-Type-Options', 'nosniff'),
        ])
        # TODO: Add explanation about write() - why it's bad to use it, why we
        # use it anyway, and why we hope it will be OK.

        connection_closed = False

        def send_json(json_object):
            nonlocal connection_closed
            if connection_closed: return
            payload = json.dumps(json_object).encode('ascii')
            header = ('%010d' % len(payload)).encode('ascii')
            try:
                write(header + payload)
            except OSError:
                connection_closed = True
                raise

        rpc_handle_exceptions(request, send_json)

        return []

    return wsgi_response


def get_routes():
    yield Rule('/rpc', methods=['POST'], endpoint=rpc_handle_partials)
