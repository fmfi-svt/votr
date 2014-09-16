
import traceback
from werkzeug.exceptions import InternalServerError
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


def finish_login(request, destination, params):
    do_logout(request)

    server = request.app.settings.servers[int(params['server'])]

    if params['type'] == 'cosignproxy':
        name = request.environ['COSIGN_SERVICE']
        fladgejt_params = dict(type='cosignproxy',
                               cosign_proxy=request.app.settings.cosign_proxy,
                               cosign_service=(name, request.cookies[name]))
    else:
        fladgejt_params = params

    try:
        client = create_client(server, fladgejt_params)
    except Exception:
        return sessions.set_cookie(request, None,
            app_response(request, error=traceback.format_exc(),
                         destination=destination))

    csrf_token = sessions.generate_key()
    session = dict(csrf_token=csrf_token, credentials=params, client=client)
    sessid = sessions.create(request, session)
    return sessions.set_cookie(request, sessid,
        app_response(request, csrf_token=csrf_token, destination=destination))


def proxylogin(request):
    if request.remote_user is None:
        raise InternalServerError(
            '/proxylogin is supposed to have "CosignAllowPublicAccess Off"')

    return finish_login(request, request.args['destination'],
        dict(type='cosignproxy', server=request.args['server']))


def start_login(request, destination, params):
    if params['type'] == 'cosignproxy':
        args = dict(server=params['server'], destination=destination)
        response = redirect(request.url_adapter.build(proxylogin, args))

        # Every login should be a complete reset, since we only do this when we
        # cannot connect. It wouldn't be good if we tried to renew our proxy
        # cookies, only for mod_cosign to think we're still logged in. So we
        # remove our own cosign cookie to ensure everything is renewed.
        cosign_service = request.environ.get('COSIGN_SERVICE')
        if cosign_service: response.delete_cookie(cosign_service)

        return response

    return finish_login(request, destination, params)


def login(request):
    params = request.values.to_dict()
    return start_login(request, params.pop('destination'), params)


def reset(request):
    destination = request.args['destination']
    credentials = None

    try:
        with sessions.transaction(request) as session:
            credentials = session['credentials']
    except Exception:
        pass

    if not credentials:
        return app_response(request, invalid_session=True,
                            destination=destination)

    do_logout(request)
    # TODO: We should enforce removing the session cookie.

    return start_login(request, destination, credentials)


def logout(request):
    do_logout(request)

    cosign_service = request.environ.get('COSIGN_SERVICE')
    if cosign_service and request.cookies.get(cosign_service):
        response = sessions.set_cookie(request, None, redirect(
            request.app.settings.cosign_proxy_logout + '?' + request.url_root))
        response.delete_cookie(cosign_service)
        return response

    return sessions.set_cookie(request, None, redirect(request.url_root))


def get_routes():
    yield Rule('/proxylogin', methods=['GET'], endpoint=proxylogin)
    yield Rule('/login', methods=['POST'], endpoint=login)
    yield Rule('/reset', methods=['POST'], endpoint=reset)
    yield Rule('/logout', methods=['POST'], endpoint=logout)
