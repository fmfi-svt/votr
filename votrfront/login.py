
from base64 import b64decode, b64encode
from datetime import datetime
import traceback
from werkzeug.contrib.sessions import generate_key
from werkzeug.exceptions import InternalServerError
from werkzeug.routing import Rule
from werkzeug.utils import redirect
from aisikl.context import Logger
from fladgejt.login import create_client
from . import sessions
from .front import app_response


def load_credentials(credentials):
    return {k: b64decode(v).decode('utf8') if k == 'password' else v
            for k, v in credentials.items()}


def save_credentials(credentials):
    return {k: b64encode(v.encode('utf8')) if k == 'password' else v
            for k, v in credentials.items()}


def do_logout(request):
    credentials = None

    try:
        with sessions.logged_transaction(request) as session:
            credentials = load_credentials(session['credentials'])
            log = session['client'].context.log
            try:
                log('logout', 'Logout started', request.full_path)
                ais_logout_suffix = request.app.settings.ais_cosign_logout
                session['client'].logout(ais_logout_suffix)
            except Exception as e:
                log('logout',
                    'Logout failed with {}'.format(type(e).__name__),
                    traceback.format_exc())
                # But delete the session anyway.
            else:
                log('logout', 'Logout finished')
            sessions.delete(request)
            # When the with statement ends, the session dict is still written
            # to the open session fd, but the file was already deleted.
    except Exception:
        pass

    return credentials


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

    sessid = datetime.utcnow().strftime('%Y%m%d_') + generate_key()
    with sessions.lock(request.app, sessid), \
            sessions.open_log_file(request, sessid) as log_file:
        logger = Logger()
        logger.log_file = log_file

        try:
            logger.log('login', 'Login started',
                [server.get('title'), params.get('type'), destination])
            ais_login_suffix = request.app.settings.ais_cosign_login
            client = create_client(server, fladgejt_params, ais_login_suffix,
                                   logger=logger)
            csrf_token = generate_key()
            session = dict(
                csrf_token=csrf_token, credentials=save_credentials(params),
                client=client)
            sessions.create(request, sessid, session)
        except Exception as e:
            error = traceback.format_exc()
            logger.log('login',
                'Login failed with {}'.format(type(e).__name__), error)
            response = app_response(request,
                server=int(params['server']), type=params['type'],
                error=error, destination=destination)
            return sessions.set_session_cookie(request, response, None)

        logger.log('login', 'Login finished')

    response = app_response(request,
        csrf_token=csrf_token, destination=destination)
    return sessions.set_session_cookie(request, response, sessid)


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
    credentials = do_logout(request)

    if not credentials:
        return app_response(request, invalid_session=True,
                            destination=destination)

    # TODO: We should enforce removing the session cookie.

    return start_login(request, destination, credentials)


def logout(request):
    do_logout(request)

    cosign_service = request.environ.get('COSIGN_SERVICE')
    if cosign_service and request.cookies.get(cosign_service):
        response = redirect(
            request.app.settings.cosign_proxy_logout + '?' + request.url_root)
        response.delete_cookie(cosign_service)
        return sessions.set_session_cookie(request, response, None)

    response = redirect(request.url_root)
    return sessions.set_session_cookie(request, response, None)


def get_routes():
    yield Rule('/proxylogin', methods=['GET'], endpoint=proxylogin)
    yield Rule('/login', methods=['POST'], endpoint=login)
    yield Rule('/reset', methods=['POST'], endpoint=reset)
    yield Rule('/logout', methods=['POST'], endpoint=logout)
