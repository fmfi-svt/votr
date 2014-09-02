
from werkzeug.exceptions import BadRequest, InternalServerError
from werkzeug.routing import Rule
from werkzeug.utils import redirect
from . import sessions


def get_login_types(request, server):
    if 'cosign' in server:
        if request.app.settings.cosign_proxy:
            return ('cosignpassword', 'cosigncookie', 'cosignproxy')
        return ('cosignpassword', 'cosigncookie')
    if 'ais_url' in server:
        return ('plainpassword',)
    return ('demo',)


def do_login(request):
    server = request.app.settings.servers[int(request.args['server'])]
    login_type = request.args['type']
    destination = request.args['to']

    if login_type not in get_login_types(request, server):
        raise BadRequest('Unsupported login type')

    sessions.delete(request, request.cookies.get(request.app.session_name))

    # TODO: create client
    from test1 import ctx
    from fladgejt.webui import WebuiClient
    client = WebuiClient(ctx)
    success = True

    if success:
        session = { 'client': client }
        sessid = sessions.create(request, session)
        response = redirect(request.url_root + '#' + destination)
        response.set_cookie(request.app.session_name, sessid)
        return response
    else:
        response = redirect(request.url_root + '#failed')
        response.delete_cookie(request.app.session_name)
        return response


def login(request):
    if request.args['type'] == 'cosignproxy':
        url = request.url_adapter.build(proxylogin, request.args)
        response = redirect(url)

        # Every login should be a complete reset, since we only do this when we
        # cannot connect. It wouldn't be good if we tried to renew our proxy
        # cookies, only for mod_cosign to think we're still logged in. So we
        # remove our own cosign cookie to ensure everything is renewed.
        cosign_service = request.environ.get('COSIGN_SERVICE')
        if cosign_service: response.delete_cookie(cosign_service)

        return response

    return do_login(request)


def proxylogin(request):
    if request.remote_user is None:
        raise InternalServerError(
            '/proxylogin is supposed to have "CosignAllowPublicAccess Off"')

    return do_login(request)


def logout(request):
    # TODO: should we also log out from AIS?

    sessions.delete(request, request.cookies.get(request.app.session_name))

    cosign_service = request.environ.get('COSIGN_SERVICE')
    if cosign_service and request.cookies.get(cosign_service):
        response = redirect(cosign_logout_url)   # TODO
        response.delete_cookie(cosign_service)
        return response

    return redirect(request.base_url)


def get_routes():
    yield Rule('/login', methods=['POST'], endpoint=login)
