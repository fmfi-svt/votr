
import os
import requests
from aisikl.context import Context, Logger
from fladgejt.flashback import FlashbackClient
from fladgejt.hybrid import HybridClient
from fladgejt.rest import RestClient
from fladgejt.webui import WebuiClient


def parse_cookie_string(cookie, cookie_name):
    parts = cookie.strip().strip('"').split(';')
    parts = [part.strip() for part in parts
             if '=' not in part or part.strip().startswith(cookie_name + '=')]
    if len(parts) > 1:
        raise ValueError("Multiple cookies named {}".format(cookie_name))
    if not parts:
        raise ValueError("Cookie value for {} not found".format(cookie_name))

    _, _, value = parts[0].rpartition('=')
    return value


def get_login_session(logger):
    def log_redirects(response, *args, **kwargs):
        if response.is_redirect:
            a, b, c = response.headers['Location'].partition('=')
            logger.log('http', 'Received {} redirect to {}{}{}'.format(
                response.status_code, a, b, '...' if c else ''))

    session = requests.Session()
    session.hooks['response'].append(log_redirects)

    def send_request(method, url, **kwargs):
        logger.log('http', 'Requesting {} {}'.format(method, url))
        response = session.request(method, url, **kwargs)
        response.raise_for_status()
        logger.log('http', 'Received response', response.text)
        return response

    return session, send_request


def get_cosign_cookies(server, params, logger):
    result = {}

    if params['type'] == 'cosignpassword':
        if 'ais_url' in server:
            url = server['ais_url'] + server['ais_login_path']
        else:
            url = server['rest_url']

        session, send_request = get_login_session(logger)
        response = send_request('GET', url)
        if '/cosign.cgi' not in response.text:
            raise Exception("Opening the Cosign login page was unsuccessful.")
        form_submit_url = response.url.partition('?')[0] + 'cosign.cgi'
        response = send_request('POST', form_submit_url, data=dict(
            login=params['username'], password=params['password'], ref=url))
        if 'ais_url' in server and 'rest_url' in server:
            send_request('GET', server['rest_url'])

        for key in ('ais_cookie', 'rest_cookie'):
            if key in server:
                result[server[key]] = session.cookies[server[key]]

    if params['type'] == 'cosignproxy':
        # http://webapps.itcs.umich.edu/cosign/index.php/Using_Proxy_Cookies
        name, value = params['cosign_service']
        filename = name + '=' + value.partition('/')[0]
        with open(os.path.join(params['cosign_proxy'], filename)) as f:
            for line in f:
                # Remove starting "x" and everything after the space.
                name, _, value = line[1:].split()[0].partition('=')
                # When connecting to the javacosign filter instead of apache's
                # mod_cosign, we have to add a sufficiently large timestamp.
                # Apache: grep cookietime filters/apache2/mod_cosign.c
                # Java: grep -ER 'parseCosignCookie|cosignCookie.getTimestamp'
                # We currently assume that REST API always uses javacosign.
                if name == server.get('rest_cookie') and '/' not in value:
                    value += '/99999999999999'
                result[name] = value

    if params['type'] == 'cosigncookie':
        for key in ('ais_cookie', 'rest_cookie'):
            if key not in server: continue
            name = server[key]
            result[name] = parse_cookie_string(params[key], name)

    return result


def create_client(server, params, *, logger=None):
    logger = logger or Logger()

    if params['type'] not in server['login_types']:
        raise ValueError("Unsupported login type")

    # If type is cosigncookie, but we only know ais_cookie, skip REST login.
    if (params['type'] == 'cosigncookie' and 'rest_cookie' in server and
            not (params.get('rest_cookie') or '').strip()):
        logger.log('login', 'Skipping REST login because rest_cookie is empty')
        server = server.copy()
        server.pop('rest_url', None)
        server.pop('rest_cookie', None)

    # Do the cosign login if required.
    cookies = get_cosign_cookies(server, params, logger)

    ctx = Context(cookies,
                  ais_url=server.get('ais_url'),
                  rest_url=server.get('rest_url'),
                  ais_logout_path=server.get('ais_logout_path'),
                  logger=logger)

    # Request ais_login_path to start the AIS session.
    if 'ais_url' in server:
        data = {}
        if params['type'] == 'plainpassword':
            data['login'] = params['username']
            data['password'] = params['password']
        soup = ctx.request_html(
            server['ais_login_path'], method='POST', data=data)
        username_element = soup.find(class_='user-name')
        if not (username_element and username_element.get_text().strip()):
            raise Exception('AIS login unsuccessful.')

    # Create the client.
    if 'ais_url' in server and 'rest_url' in server:
        client = HybridClient(ctx)
    elif 'ais_url' in server:
        client = WebuiClient(ctx)
    elif 'rest_url' in server:
        client = RestClient(ctx)
    else:
        if params['type'] == 'flashback':
            client = FlashbackClient(ctx, server['flashbacks_dir'], params['file'])
        else:
            raise Exception('Unsupported type: %r' % params['type'])

    # Check that login was successful.
    client.check_connection()

    return client
