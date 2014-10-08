
import json
import traceback
from werkzeug.routing import Rule
from . import sessions
from fladgejt.helpers import encode_key, decode_key


def decode_args(method, args):
    spec = getattr(method, 'key_args', None)
    if not spec: return args
    return tuple(decode_key(arg) if is_key and isinstance(arg, str) else arg
                 for arg, is_key in zip(args, spec))


def encode_result(thing):
    if (isinstance(thing, tuple) and hasattr(thing, '_replace') and
        hasattr(thing, 'key')):
        thing = thing._replace(key=encode_key(thing.key))
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

    log('rpc', 'RPC {} started'.format(name), args)
    try:
        method = getattr(session['client'], name)
        args = decode_args(method, args)
        result = encode_result(method(*args))
    except Exception as e:
        log('rpc', 'RPC {} failed with {}'.format(name, type(e).__name__),
            traceback.format_exc())
        raise
    log('rpc', 'RPC {} finished'.format(name), result)
    return result


def rpc_handle_sessions(request, send_json):
    if not sessions.get_cookie(request):
        raise ValueError('Session cookie not found')

    def custom_log(type, message, data=None):
        send_json({ 'log': type, 'message': message })
        # TODO: also write to log file.

    with sessions.transaction(request) as session:
        if request.headers.get('X-CSRF-Token') != session['csrf_token']:
            raise ValueError('Bad X-CSRF-Token value')
        session['client'].context.log = custom_log
        result = rpc_handle_call(request, session)
        del session['client'].context.log

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
        write = start_response('200 OK', [('Content-Type', 'text/plain')])
        # TODO: Add explanation about write() - why it's bad to use it, why we
        # use it anyway, and why we hope it will be OK.

        def send_json(json_object):
            payload = json.dumps(json_object).encode('ascii')
            header = ('%010d' % len(payload)).encode('ascii')
            write(header + payload)

        rpc_handle_exceptions(request, send_json)

        return []

    return wsgi_response


def get_routes():
    yield Rule('/rpc', methods=['POST'], endpoint=rpc_handle_partials)
