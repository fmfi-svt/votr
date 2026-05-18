from base64 import b64decode, b64encode
from contextlib import AsyncExitStack
from datetime import datetime, UTC
import hashlib
import logging
import os
import traceback
import re
from starlette.exceptions import HTTPException
from starlette.routing import Route
from starlette.responses import Response, RedirectResponse
from aisikl.context import Logger
from fladgejt.login import create_client
from votrfront import sessions
from votrfront.base import var_path
from votrfront.front import app_response
from votrfront.utils import check_header

try:
    from onelogin.saml2.auth import OneLogin_Saml2_Auth
    from onelogin.saml2.settings import OneLogin_Saml2_Settings
    from onelogin.saml2.idp_metadata_parser import OneLogin_Saml2_IdPMetadataParser
    saml_imported = True
except ImportError:
    saml_imported = False

pylogger = logging.getLogger(__name__)


def build_saml_settings(votr_settings):
    if not saml_imported:
        return 'python3-saml is not installed'
    idp_metadata_path = var_path('saml/idp-metadata.xml')
    if not idp_metadata_path.exists():
        return 'idp-metadata.xml not found'

    settings_dict = {
        'sp': {
            'entityId': votr_settings.root_url + 'saml_sp',
            'assertionConsumerService': {
                'url': votr_settings.root_url + 'saml_acs',
            },
            'singleLogoutService': {
                'url': votr_settings.root_url + 'saml_logout',
            },
        },
        'security': {
            # python3-saml default is just 2 days.
            'metadataValidUntil': '',
            # python3-saml default is "PT604800S" (1 week). I don't really know
            # what it means, but other SAML SPs don't have it.
            'metadataCacheDuration': '',
            # "Want" is a too strong word, but if not enabled, python3-saml only
            # generates a <KeyDescriptor use="signing">. Shibboleth IdP fails if
            # a <KeyDescriptor use="encryption"> (or without use="") is missing.
            'wantAssertionsEncrypted': True,
            # Rejecting SHA1 sounds like a good idea. I don't know why it isn't
            # enabled by default.
            'rejectDeprecatedAlgorithm': True,
            # "The <LogoutRequest> message MUST be signed if the HTTP POST or
            # Redirect binding is used." Shibboleth IdP rejects it if it's not
            # signed. I don't know why this isn't enabled by default.
            'logoutRequestSigned': True,
            'logoutResponseSigned': True,
        },
        'organization': {
            'en': {
                'name': 'Comenius University in Bratislava',
                'displayname': 'Comenius University',
                'url': 'http://uniba.sk/en',
            },
            'sk': {
                'name': 'Univerzita Komenského v Bratislave',
                'displayname': 'Univerzita Komenského',
                'url': 'http://uniba.sk/',
            },
        },
        # Probably not 'debug', because it prints to stdout and changes global
        # state with xmlsec.enable_debug_trace().
    }

    idp_metadata = idp_metadata_path.read_bytes()
    settings_dict = OneLogin_Saml2_IdPMetadataParser.merge_settings(
        settings_dict, OneLogin_Saml2_IdPMetadataParser.parse(idp_metadata))

    return OneLogin_Saml2_Settings(
        settings=settings_dict,
        custom_base_path=str(var_path('saml')),
    )


def build_saml_auth(request, *, post_data):
    saml_settings = request.state['saml_settings']
    if isinstance(saml_settings, str):
        raise Exception(saml_settings)

    request_data = {
        'http_host': request.url.hostname,

        # Despite the name, this should be the full path without query string.
        # (Looks like 'path_info' could work too, but that is undocumented.)
        'script_name': request.url.path,

        # python3-saml README says `"get_data": "", "post_data": "",` but they
        # really should be dicts.
        # Grepping python3-saml source shows that post_data is only read by
        # OneLogin_Saml2_Auth.process_response(). Elsewhere, {} is enough.
        'get_data': request.query_params,
        'post_data': post_data,

        # It really is 'on'/'off'. Yuck!
        'https': 'on' if request.url.is_secure else 'off',

        # These are optional according to the python3-saml README, but it should
        # slightly improve proper SAML spec compliance. "The relying party MUST
        # therefore perform the verification step using the original URL-encoded
        # values it received on the query string."
        'validate_signature_from_qs': True,
        'query_string': request.url.query,

        # python3-saml README mentions 'request_uri', but it's only read by
        # OneLogin_Saml2_Utils.{get_self_routed_url_no_query,get_self_url} which
        # are never called.
    }

    return OneLogin_Saml2_Auth(
        request_data=request_data,
        old_settings=saml_settings,
    )


async def saml_sp(request):
    instance_title = request.state['settings'].instance_title
    saml_settings = request.state['saml_settings']
    if isinstance(saml_settings, str):
        raise Exception(saml_settings)

    metadata = saml_settings.get_sp_metadata()

    # The python3-saml default <NameIDFormat> prints a warning in Shibboleth IdP
    # logs: "Ignoring NameIDFormat metadata that includes the 'unspecified'
    # format".
    # Other SPs don't have any <NameIDFormat> in metadata.
    # It can't be removed in python3-saml settings_dict. We must hack it out.
    metadata = re.sub(br' *<md:NameIDFormat>\S*</md:NameIDFormat>\n', b'',
        metadata)

    # Add mdui:UIInfo manually. python3-saml isn't able to generate it.
    mdui = f'''
        <md:Extensions>
            <mdui:UIInfo xmlns:mdui="urn:oasis:names:tc:SAML:metadata:ui">
                <mdui:DisplayName xml:lang="en">{instance_title}</mdui:DisplayName>
                <mdui:DisplayName xml:lang="sk">{instance_title}</mdui:DisplayName>
            </mdui:UIInfo>
        </md:Extensions>
    '''
    metadata = re.sub(
        br' *<md:KeyDescriptor',
        (lambda matchobj: mdui.encode('utf8') + matchobj.group(0)),
        metadata, count=1, flags=re.DOTALL)

    if (errors := saml_settings.validate_metadata(metadata)):
        raise Exception(repr(errors))

    return Response(metadata, media_type='application/samlmetadata+xml')


def generate_key():
    return hashlib.sha1(os.urandom(30)).hexdigest()


_TEMPORARY_PARAMS = {
    'destination',
    'my_entity_id',
    'andrvotr_api_key',
    'andrvotr_authority_token',
}


def load_credentials(credentials):
    return {k: b64decode(v).decode('utf8') if k == 'password' else v
            for k, v in credentials.items()}


def save_credentials(credentials):
    return {k: b64encode(v.encode('utf8')) if k == 'password' else v
            for k, v in credentials.items()
            if k not in _TEMPORARY_PARAMS}


async def do_logout(request):
    credentials = None

    try:
        async with sessions.logged_transaction(request) as session:
            credentials = load_credentials(session['credentials'])
            log = session['client'].context.log
            try:
                await log('logout', 'Logout started', str(request.url))
                await session['client'].logout()
            except BaseException as e:
                await log('logout',
                    f'Logout failed with {type(e).__name__}',
                    traceback.format_exc())
                raise
                # But delete the session anyway.
            else:
                await log('logout', 'Logout finished')
            finally:
                sessions.delete(request)
            # When the `async with` statement ends, the session dict is still
            # written to the open session fd, but the file was already deleted.
    except Exception:
        pass

    request.state['votr_cookie_value'] = {}

    return credentials


async def finish_login(request, get_params):
    settings = request.state['settings']

    await do_logout(request)

    params = None
    server = None
    destination = None

    sessid = datetime.now(UTC).strftime('%Y%m%d_') + generate_key()
    async with AsyncExitStack() as stack:
        await stack.enter_async_context(sessions.lock(sessid))
        logger = Logger()
        logger.log_file = stack.enter_context(sessions.open_log_file(sessid))

        try:
            await logger.log('login', 'Login started')
            params = get_params()
            server = settings.servers[int(params['server'])]
            destination = params['destination']
            await logger.log('login', 'Creating client', {
                'server_title': server.get('title'),
                'type': params['type'],
                'destination': destination,
            })
            client = await create_client(server, params, logger=logger)
            csrf_token = generate_key()
            session = dict(
                last_announcement=settings.announcement_html,
                csrf_token=csrf_token,
                credentials=save_credentials(params),
                client=client,
            )
            sessions.create(request, sessid, session)
        except Exception as e:
            error = traceback.format_exc()
            await logger.log(
                'login', f'Login failed with {type(e).__name__}', error)
            app_kwargs = { 'error': error, 'destination': destination or '' }
            if server:
                app_kwargs['server'] = params['server']
                if 'type' in params and params['type'] in server['login_types']:
                    app_kwargs['type'] = params['type']
            return await app_response(request, **app_kwargs)

        await logger.log('login', 'Login finished', params.get('username'))

    request.state['votr_cookie_value'] = dict(sessid=sessid)

    # TODO: This condition is duplicated with main.tsx.
    redirect_url = str(request.base_url)
    if destination and destination.startswith('?'):
        redirect_url += destination
    return RedirectResponse(redirect_url, 303)


def _read_saml_attribute(auth, name):
    values = auth.get_attribute(name)
    if not values:
        return None
    if len(values) > 1:
        raise Exception(f'Multiple {name} attribute values')
    return values[0]


def build_params_from_saml_response(request, post_data, votr_cookie_value):
    login_request_id = votr_cookie_value['login_request_id']
    server = votr_cookie_value['server']
    destination = votr_cookie_value['destination']

    # Remembering request_id in a cookie protects against "login CSRF". In this
    # attack, the attacker forces a victim to log in to the attacker's account,
    # possibly without the victim noticing. On some sites this can be a real
    # issue, but on Votr it wouldn't be very serious anyway.
    auth = build_saml_auth(request, post_data=post_data)
    auth.process_response(request_id=login_request_id)

    if (errors := auth.get_errors()):
        if (error_reason := auth.get_last_error_reason()):
            errors.append(error_reason)
        raise Exception(f'SAML login failed: {errors!r}')

    andrvotr_authority_token = _read_saml_attribute(
        auth, 'tag:fmfi-svt.github.io,2024:andrvotr-authority-token')
    if not andrvotr_authority_token:
        raise Exception(
            'IdP did not provide the Andrvotr authority token')

    uid = _read_saml_attribute(auth, 'urn:oid:0.9.2342.19200300.100.1.1')

    andrvotr_api_key = var_path('saml/andrvotr_api_key').read_text().strip()

    # TODO: One day: comply with SessionNotOnOrAfter (get_session_expiration).

    return dict(
        server=server,
        type='saml_andrvotr',
        destination=destination,
        my_entity_id=auth.get_settings().get_sp_data()['entityId'],
        andrvotr_api_key=andrvotr_api_key,
        andrvotr_authority_token=andrvotr_authority_token,
        username=uid,  # Only used for logging.
        saml_logout_kwargs=dict(
            name_id=auth.get_nameid(),
            session_index=auth.get_session_index(),
            nq=auth.get_nameid_nq(),
            name_id_format=auth.get_nameid_format(),
            spnq=auth.get_nameid_spnq(),
        ),
    )


async def _get_form(request):
    # `FormData` inherits from `ImmutableMultiDict[str, UploadFile | str]`. We
    # don't use files or multi-valued keys.
    # This ct() always succeeds, and FormData.close() is a no-op, because
    # starlette/formparsers.py never creates UploadFile if max_files == 0.
    async with request.form(max_files=0) as form:
        return { k: ct(str, v) for k, v in form.items() }


async def saml_acs(request):
    check_header(request, 'Sec-Fetch-Mode', { 'navigate' })
    check_header(request, 'Sec-Fetch-Dest', { 'document' })

    post_data = await _get_form(request)

    # do_logout() overwrites it. Stash the original value.
    old_votr_cookie_value = request.state['votr_cookie_value']

    # Do all SAML response processing inside finish_login() and use its error
    # handling. If it throws for any reason, we want to write the exception to
    # Votr logs and show the login form again.
    return await finish_login(request, lambda: build_params_from_saml_response(
        request, post_data, old_votr_cookie_value))


async def start_login(request, params):
    if params['type'] == 'saml_andrvotr':
        await do_logout(request)

        auth = build_saml_auth(request, post_data={})
        redirect_url = auth.login('')
        request.state['votr_cookie_value'] = dict(
            login_request_id=auth.get_last_request_id(),
            server=params['server'],
            destination=params['destination'],
        )
        return RedirectResponse(redirect_url, 303)

    return await finish_login(request, lambda: params)


async def login(request):
    check_header(request, 'Sec-Fetch-Site', { 'none', 'same-origin' })
    check_header(request, 'Sec-Fetch-Mode', { 'navigate' })
    check_header(request, 'Sec-Fetch-Dest', { 'document' })

    post_data = await _get_form(request)
    params = { 'destination': '', **post_data }
    return await start_login(request, params)


async def reset(request):
    check_header(request, 'Sec-Fetch-Site', { 'none', 'same-origin' })
    check_header(request, 'Sec-Fetch-Mode', { 'navigate' })
    check_header(request, 'Sec-Fetch-Dest', { 'document' })

    try:
        destination = request.query_params['destination']
    except KeyError:
        raise HTTPException(400) from None

    credentials = await do_logout(request)

    if not credentials:
        return await app_response(
            request, invalid_session=True, destination=destination)

    params = { **credentials, 'destination': destination }
    return await start_login(request, params)


async def saml_logout(request):
    # Extensively documented at:
    # https://github.com/fmfi-svt/votr/wiki/SAML#logout
    try:
        auth = build_saml_auth(request, post_data={})
        url = auth.process_slo()

        if (errors := auth.get_errors()):
            if (error_reason := auth.get_last_error_reason()):
                errors.append(error_reason)
            raise Exception(f'SAML logout failed: {errors!r}')

        if url:
            # https://github.com/fmfi-svt/votr/wiki/SAML#externally-initiated-logout
            await do_logout(request)
            return RedirectResponse(url, 303)
        else:
            # https://github.com/fmfi-svt/votr/wiki/SAML#votr-initiated-logout
            return Response('Logout successful.')
    except Exception as e:
        pylogger.exception('/saml_logout failed')
        raise HTTPException(500, f'Logout error: {e}') from e


async def logout(request):
    check_header(request, 'Sec-Fetch-Site', { 'none', 'same-origin' })
    check_header(request, 'Sec-Fetch-Mode', { 'navigate' })
    check_header(request, 'Sec-Fetch-Dest', { 'document' })

    credentials = await do_logout(request)

    redirect_url = str(request.base_url)
    if credentials:
        saml_logout_kwargs = credentials.get('saml_logout_kwargs')
        if saml_logout_kwargs is not None:
            try:
                auth = build_saml_auth(request, post_data={})
                redirect_url = auth.logout(**saml_logout_kwargs)
            except Exception:
                pylogger.exception('SAML auth.logout() failed')
                # Exceptions in building the logout request XML should be rare.
                # As a low effort compromise, ignore SAML, redirect to our root,
                # and delete at least our own session.

    return RedirectResponse(redirect_url, 303)


routes = [
    Route('/saml_sp', methods=['GET'], endpoint=saml_sp),
    Route('/saml_acs', methods=['POST'], endpoint=saml_acs),
    Route('/saml_logout', methods=['GET'], endpoint=saml_logout),
    Route('/login', methods=['POST'], endpoint=login),
    Route('/reset', methods=['POST'], endpoint=reset),
    Route('/logout', methods=['POST'], endpoint=logout),
]
