
import traceback
from werkzeug.exceptions import BadRequest, InternalServerError
from werkzeug.routing import Rule
from werkzeug.utils import redirect
from fladgejt.login import create_client
from . import sessions
from .front import app_response


def do_logout(request):
    try:
        with sessions.transaction(request) as session:
            session['client'].logout()
    except Exception:
        pass

    sessions.delete(request)


def do_login(request, params):
    do_logout(request)

    params = dict(params)

    server = request.app.settings.servers[int(params['server'])]
    destination = params['to']

    if params['type'] == 'cosignproxy':
        name = request.environ['COSIGN_SERVICE']
        params['cosign_service'] = (name, request.cookies[name])

    try:
        client = create_client(request.app.settings, server, params)
    except Exception:
        return sessions.set_cookie(request, None,
            app_response(request, login=True, error=traceback.format_exc(),
                         destination=destination))

    # TODO: only store real keys in credentials?
    params.pop('to')
    params.pop('votr_cookie', None)

    session = { 'credentials': params, 'client': client }
    sessid = sessions.create(request, session)
    return sessions.set_cookie(request, sessid,
        app_response(request, destination=destination))


def login(request, params=None):
    if not params:
        params = request.values.to_dict()

    if params['type'] == 'cosignproxy':
        response = redirect(request.url_adapter.build(
            proxylogin, server=params['server'], to=params['to']))

        # Every login should be a complete reset, since we only do this when we
        # cannot connect. It wouldn't be good if we tried to renew our proxy
        # cookies, only for mod_cosign to think we're still logged in. So we
        # remove our own cosign cookie to ensure everything is renewed.
        cosign_service = request.environ.get('COSIGN_SERVICE')
        if cosign_service: response.delete_cookie(cosign_service)

        return response

    return do_login(request, params)


def proxylogin(request):
    if request.remote_user is None:
        raise InternalServerError(
            '/proxylogin is supposed to have "CosignAllowPublicAccess Off"')

    return do_login(request, dict(request.args, type='proxylogin'))


def reset(request):
    destination = request.args['to']
    credentials = None

    try:
        with sessions.transaction(request) as session:
            credentials = session['credentials']
    except Exception:
        pass

    if not credentials:
        return app_response(request, login=True, invalid_session=True,
                            destination=destination)

    do_logout(request)
    # TODO: We should enforce removing the session cookie.

    return login(request, dict(credentials, to=destination))


def logout(request):
    do_logout(request)

    cosign_service = request.environ.get('COSIGN_SERVICE')
    if cosign_service and request.cookies.get(cosign_service):
        response = sessions.set_cookie(request, None, redirect(
            request.app.settings.cosign_url + 'logout.cgi?' + request.url_root))
        response.delete_cookie(cosign_service)
        return response

    return sessions.set_cookie(request, None, redirect(request.url_root))


def get_routes():
    yield Rule('/login', methods=['POST'], endpoint=login)
    yield Rule('/proxylogin', methods=['GET'], endpoint=proxylogin)
    yield Rule('/reset', methods=['POST'], endpoint=reset)
    yield Rule('/logout', methods=['POST'], endpoint=logout)
