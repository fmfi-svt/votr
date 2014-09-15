
import os
import json
import traceback
from werkzeug.exceptions import BadRequest
from werkzeug.routing import Rule
from . import sessions


def rpc_handle_call(request, session):
    name = request.args['name']
    args = json.loads(request.get_data(as_text=True))

    return getattr(session['client'], name)(*args)


def rpc_handle_sessions(request, send_json):
    if not sessions.get_cookie(request):
        raise BadRequest('Session cookie not found')

    def custom_log(type, message, data=None):
        send_json({ 'log': type, 'message': message })
        # TODO: also write to log file.

    with sessions.transaction(request) as session:
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
