
import re
from urllib.parse import urljoin
from aisikl.context import Context, Logger
from fladgejt.flashback import FlashbackClient
from fladgejt.hybrid import HybridClient
from fladgejt.rest import RestClient
from fladgejt.webui import WebuiClient


# Omit cookie values and query string values from logs.
_redact_values_re = re.compile(r'=[^?&;]{10,}')
_redact_values_sub = r'=[...]'


# Log most cookie names, but omit some known non-constant names, just in case.
_redact_names_re = re.compile(r'(pastr-|opensaml_req_ss|shibsession_)[^=]*=')
_redact_names_sub = r'\1[...]='


def _redact(string):
    string = _redact_values_re.sub(_redact_values_sub, string)
    string = _redact_names_re.sub(_redact_names_sub, string)
    return string


# Omit the value="" HTML attribute from logged response bodies.
_value_attr_q_re = re.compile(r'(value)="[^"]{10,}"', re.IGNORECASE)
_value_attr_q_sub = r'\1="[...]"'
_value_attr_a_re = re.compile(r"(value)='[^']{10,}'", re.IGNORECASE)
_value_attr_a_sub = r"\1='[...]'"


def _redact_response(response):
    # https://github.com/psf/requests/issues/3957 :(
    headers = '\n'.join(
        f'{k}: {_redact(v)}' for k, v in response.raw.headers.items())
    if response.is_redirect:
        return headers
    if not response.headers.get('content-type', '').startswith('text/'):
        return headers
    text = response.text
    text = _value_attr_q_re.sub(_value_attr_q_sub, text)
    text = _value_attr_a_re.sub(_value_attr_a_sub, text)
    return headers + '\n---\n' + text


_samlsso_re = re.compile(r'^https://[^/]+/ais/sso/samlsso\?')


def _send_request(ctx, url, data):
    method = 'POST' if data else 'GET'

    redacted_data = { k: '[...]' for k in data } if data else data
    ctx.log('http', f'Requesting {method} {_redact(url)}', redacted_data)

    response = ctx.requests_session.request(
        method, url, data=data, allow_redirects=False)

    # Work around a missing Content-Type header on /ais/sso/samlsso.
    # We read the header in _redact_response and _send_request_chain.
    if (_samlsso_re.match(url) and 'content-type' not in response.headers and
            response.content.startswith(b'<html>')):
        response.headers['content-type'] = 'text/html; charset=UTF-8'

    # Log headers and body together in one string, for nicer `log view`.
    ctx.log(
        'http', f'Received HTTP {response.status_code} response',
        _redact_response(response))

    response.raise_for_status()

    return response


def _parse_form(old_url, soup):
    forms = soup.find_all('form')
    if len(forms) != 1:
        raise Exception(f'Unexpected number of form elements: {len(forms)}')
    url = urljoin(old_url, forms[0]['action'])
    data = {}
    for elem in forms[0].find_all('input'):
        if elem.get('type') == 'hidden':
            data[elem['name']] = elem.get('value', '')
    for elem in forms[0].find_all('input') + forms[0].find_all('button'):
        if elem.get('type') == 'submit':
            if elem.get('name'):
                data[elem['name']] = elem.get('value', '')
            break
    return url, data


_idp_profile_re = re.compile(r'^https://[^/]+/idp/profile/')


def _send_request_chain(ctx, params, url, data):
    count = 0
    tried_saml_password_login = False
    while True:
        count += 1
        if count > 30:
            raise Exception('Too many redirects')

        # If using Andrvotr, rewrite all requests of GET .../Redirect/SSO to
        # POST .../andrvotr/fabricate, with the necessary POST parameters.
        if params['type'] == 'saml_andrvotr' and _idp_profile_re.match(url):
            idp_host = url.split('/')[2]
            if not url.startswith(
                    f'https://{idp_host}/idp/profile/SAML2/Redirect/SSO?'):
                raise Exception(f'Unexpected IdP request to {_redact(url)}')
            if data:
                raise Exception(
                    f'Unexpected POST data for IdP request to {_redact(url)}')
            old_url = url
            url = f'https://{idp_host}/idp/profile/andrvotr/fabricate'
            data = {
                'front_entity_id': params['my_entity_id'],
                'api_key': params['andrvotr_api_key'],
                'andrvotr_authority_token': params['andrvotr_authority_token'],
                'target_url': old_url,
            }
            ctx.log('login', 'Going andrvotr', [_redact(old_url), url])

        response = _send_request(ctx, url, data)

        # Handle real HTTP 3xx redirects.
        if response.is_redirect:
            # For simplicity we assume the next request is always GET.
            # HTTP 307 and 308 are not supported correctly.
            url = response.next.url
            data = None
            continue

        # Everything except 200 (and 3xx handled above) is an error.
        if response.status_code != 200:
            raise Exception(f'Unexpected HTTP {response.status_code} status for url: {_redact(url)}')

        # TODO: Handle successful REST API login. REST API does not support
        # SAML yet.

        if response.headers.get('content-type', '').startswith('text/html'):
            soup = ctx.parse_html(response)

            # Detect successful AIS login (old interface).
            username_element = soup.find(class_='user-name')
            if username_element and username_element.get_text().strip():
                ctx.log('login', 'AIS login successful (old interface)')
                return

            # Detect successful AIS login (new interface).
            if '/ais/apps/student/' in response.url and soup.find('app-root'):
                ctx.log('login', 'AIS login successful (new interface)')
                return

            # Handle login errors for saml_password and plain_password.
            for error_class in [
                'login-error',  # used by login.do with plain_password
                'output--error',  # used by upstream Shibboleth IdP
                'error-message',  # specific to Uniba Shibboleth IdP
            ]:
                error_element = soup.find(class_=error_class)
                if error_element:
                    error_text = error_element.get_text().strip()
                    if error_text:
                        raise Exception(f'Login error: {error_text}')

            # Handle "fake redirects" - HTML pages with JavaScript code that
            # instantly submits a POST form.
            js_submit = 'document.forms[0].submit()'
            onload = (soup.body and soup.body.get('onload')) or ''
            script = (soup.script and soup.script.get_text()) or ''
            if js_submit in onload or js_submit in script:
                ctx.log('login', 'Detected a POST page')
                url, data = _parse_form(url, soup)
                continue

            if params['type'] == 'saml_password':
                # Handle Shibboleth IdP's "Loading Session Information" page.
                if soup.find('input', attrs={'name': 'shib_idp_ls_supported'}):
                    url, data = _parse_form(url, soup)
                    # Real browsers set some fields to "true". Let's cargo cult.
                    data['shib_idp_ls_supported'] = 'true'
                    for k in data:
                        if k.startswith('shib_idp_ls_success.'):
                            data[k] = 'true'
                    ctx.log('login', 'Detected a local storage page', data)
                    continue

                # Handle Shibboleth IdP's password based login form.
                if (soup.find('input', attrs={'name': 'j_username'}) and
                        soup.find('input', attrs={'name': 'j_password'})):
                    ctx.log('login', 'Detected a login form page')
                    if tried_saml_password_login:
                        raise Exception('Username and password did not work')
                    tried_saml_password_login = True
                    url, data = _parse_form(url, soup)
                    data['j_username'] = params['username']
                    data['j_password'] = params['password']
                    continue

        raise Exception('Unrecognized response during login process')


def _create_context(server, logger):
    return Context(
        ais_url=server.get('ais_url'), rest_url=server.get('rest_url'),
        logger=logger)


def _create_normal_client(ctx, server, logout_mode):
    if 'ais_url' in server and 'rest_url' in server:
        client = HybridClient(ctx)
    elif 'ais_url' in server:
        client = WebuiClient(ctx)
    elif 'rest_url' in server:
        client = RestClient(ctx)
    else:
        raise Exception('Neither ais_url nor rest_url is configured')

    client.logout_mode = logout_mode
    return client


def _login_with_saml(server, params, logger):
    ctx = _create_context(server, logger)

    if 'ais_url' in server:
        # Simulate clicking the login button. It has
        # onclick="location.href='/ais/sso/samlsso?SAML2.HTTPBinding=HTTP-POST'"
        url = server['ais_url'] + 'ais/sso/samlsso?SAML2.HTTPBinding=HTTP-POST'
        _send_request_chain(ctx, params, url, None)

    if 'rest_url' in server:
        # TODO: This is purely theoretical. REST API does not support SAML yet.
        _send_request_chain(ctx, params, server['rest_url'], None)

    logout_mode = {
        # End the AIS session, just to be polite and free up resources. But
        # don't end the IdP session we're a part of. That's up to the user and
        # should happen in their browser, especially if they also signed in to
        # other services.
        'saml_andrvotr': WebuiClient.LOGOUT_WITHOUT_REDIRECTS,
        # End the IdP session too, just to be polite. But don't run JavaScript
        # on the IdP logout page, that would be too much.
        'saml_password': WebuiClient.LOGOUT_WITH_REDIRECTS,
    }[params['type']]
    return _create_normal_client(ctx, server, logout_mode)


def _login_with_plain_password(server, params, logger):
    if 'rest_url' in server:
        raise Exception('plain_password type does not support rest_url')

    ctx = _create_context(server, logger)

    # Submit the login form. It has action="/ais/login.do".
    # On both success and failure, it will respond with 302 to ais/start.do.
    # start.do will contain either an error message or the signed in view.
    login_url = server['ais_url'] + 'ais/login.do'
    login_data = { 'login': params['username'], 'password': params['password'] }
    _send_request_chain(ctx, params, login_url, login_data)

    return _create_normal_client(ctx, server, WebuiClient.LOGOUT_WITH_REDIRECTS)


def _parse_cookie_string(ctx, base_url, default_name, cookie_string):
    # Accept either one or more ';'-separated key=value pairs, or just one
    # cookie value (assume default_name).

    if not (base_url and default_name and cookie_string):
        return

    domain = base_url.split('/')[2].split(':')[0]

    cookie_string = cookie_string.strip()

    if cookie_string and '=' not in cookie_string and ';' not in cookie_string:
        cookie_string = default_name + '=' + cookie_string

    for pair in cookie_string.split(';'):
        pair = pair.strip()
        if not pair: continue
        if '=' not in pair:
            raise ValueError(
                'Expected either a single cookie value or a list of '
                '";"-separated key=value elements, but an element does not '
                'contain "="')
        name, _, value = pair.partition('=')
        ctx.requests_session.cookies.set(name, value, domain=domain)


def _login_with_cookie(server, params, logger):
    # If login type is "cookie", but we only know ais_cookie, skip REST login.
    if ('ais_url' in server and 'rest_url' in server and
            not (params.get('rest_cookie') or '').strip()):
        logger.log('login', 'Skipping REST login because rest_cookie is empty')
        server = server.copy()
        server.pop('rest_url', None)
        server.pop('rest_cookie', None)

    ctx = _create_context(server, logger)

    _parse_cookie_string(
        ctx, server.get('ais_url'), server.get('ais_cookie'),
        params.get('ais_cookie'))

    _parse_cookie_string(
        ctx, server.get('rest_url'), server.get('rest_cookie'),
        params.get('rest_cookie'))

    return _create_normal_client(ctx, server, WebuiClient.LOGOUT_NOTHING)


def _login_with_flashback(server, params, logger):
    if 'ais_url' in server:
        raise Exception('flashback type does not support ais_url')
    if 'rest_url' in server:
        raise Exception('flashback type does not support rest_url')

    ctx = _create_context(server, logger)
    return FlashbackClient(ctx, server['flashbacks_dir'], params['file'])


_handlers = {
    'saml_andrvotr': _login_with_saml,
    'saml_password': _login_with_saml,
    'plain_password': _login_with_plain_password,
    'cookie': _login_with_cookie,
    'flashback': _login_with_flashback,
}


def create_client(server, params, *, logger=None):
    # server should be:
    #   { login_types: tuple[str],
    #     ais_url?: str, ais_cookie?: str,
    #     rest_url?: str, rest_cookie?: str,
    #     flashbacks_dir?: str }
    # (usually also has { title: str } but this function does not need it)
    #
    # params should be one of:
    #   { type: "saml_password", username: str, password: str }
    #   { type: "saml_andrvotr", my_entity_id: str, andrvotr_api_key: str,
    #     andrvotr_authority_token: str }
    #   { type: "plain_password", username: str, password: str }
    #   { type: "cookie", ais_cookie?: str|None, rest_cookie?: str|None }
    #   { type: "flashback", file: str }
    # (usually also has { server: str } but this function does not need it)

    logger = logger or Logger()

    if params['type'] not in server['login_types']:
        raise ValueError("Unsupported login type")

    handler = _handlers[params['type']]
    client = handler(server, params, logger)

    # Check that login was successful.
    client.check_connection()

    return client
