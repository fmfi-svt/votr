
import os
import requests
from aisikl.context import Context
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


def get_cosign_cookies(server, params):
    if params['type'] == 'cosignpassword':
        if 'ais_url' in server:
            url = server['ais_url'] + 'ais/login.do?'
        else:
            url = server['rest_url']

        s = requests.Session()
        r = s.get(url)
        s.post(r.url.partition('?')[0] + 'cosign.cgi', data=dict(
            login=params['username'], password=params['password'], ref=url))
        if 'ais_url' in server and 'rest_url' in server:
            s.get(server['rest_url'])

        result = {}
        if 'ais_url' in server:
            result[server['ais_cookie']] = s.cookies[server['ais_cookie']]
        if 'rest_url' in server:
            result[server['rest_cookie']] = s.cookies[server['rest_cookie']]
        return result

    if params['type'] == 'cosignproxy':
        # http://webapps.itcs.umich.edu/cosign/index.php/Using_Proxy_Cookies
        name, value = params['cosign_service']
        filename = name + '=' + value.partition('/')[0]
        result = {}
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
        return result

    if params['type'] == 'cosigncookie':
        result = {}
        for key in ('ais_cookie', 'rest_cookie'):
            if key not in server: continue
            name = server[key]
            result[name] = parse_cookie_string(params[key], name)
        return result

    return {}


def create_client(server, params):
    if params['type'] not in server['login_types']:
        raise ValueError("Unsupported login type")

    # If type is cosigncookie, but we only know ais_cookie, skip REST login.
    if (params['type'] == 'cosigncookie' and 'rest_cookie' in server and
            not (params.get('rest_cookie') or '').strip()):
        server = server.copy()
        server.pop('rest_url', None)
        server.pop('rest_cookie', None)

    # Do the cosign login if required.
    cookies = get_cosign_cookies(server, params)

    # TODO: Refactor Context arguments for REST and demo.
    ctx = Context(cookies,
                  ais_url=server.get('ais_url'),
                  rest_url=server.get('rest_url'))

    # Request login.do to start the AIS session.
    if 'ais_url' in server:
        data = {}
        if params['type'] == 'plainpassword':
            data['login'] = params['username']
            data['password'] = params['password']
        soup = ctx.request_html('/ais/login.do', method='POST', data=data)
        username_element = soup.find(class_='user-name')
        if not (username_element and username_element.get_text()):
            raise Exception('AIS login unsuccessful.')

    # Create the client.
    if 'ais_url' in server and 'rest_url' in server:
        client = HybridClient(ctx)
    elif 'ais_url' in server:
        client = WebuiClient(ctx)
    elif 'rest_url' in server:
        client = RestClient(ctx)
    else:
        raise Exception('Demo client is not supported')

    # Check that login was successful.
    client.check_connection()

    return client
