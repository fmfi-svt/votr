
import os
import requests
from requests import session
from aisikl.context import Context
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


def get_cosign_cookies(settings, server, params):
    if params['type'] == 'cosignpassword':
        data = {}
        data['login'] = params['login']
        data['password'] = params['password']
        data['ref'] = server['ais_url'] + 'ais/login.do?'
        name = server['ais_cookie']
        r = requests.get(server['cosign_url'], data={name:'', server['ais_url'] + 'ais/login.do':''})
        r = requests.post(server['cosign_url'] + 'cosign.cgi', data=data, cookies=r.cookies)
        value = r.history[3].cookies[name]
        return {name: value}

    if params['type'] == 'cosignproxy':
        # http://webapps.itcs.umich.edu/cosign/index.php/Using_Proxy_Cookies
        name, value = params['cosign_service']
        filename = name + '=' + value.partition('/')[0]
        result = {}
        with open(os.path.join(settings.cosign_proxy, filename)) as f:
            for line in f:
                # Remove starting "x" and everything after the space.
                name, value = line[1:].partition(' ')[0].partition('=')
                result[name] = value
        return result

    if params['type'] == 'cosigncookie':
        name = server['ais_cookie']
        value = parse_cookie_string(params['cookie'], name)
        return { name: value }

    raise ValueError(params['type'])


def get_login_types(settings, server):
    if 'cosign' in server:
        if settings.cosign_proxy:
            return ('cosignpassword', 'cosigncookie', 'cosignproxy')
        return ('cosignpassword', 'cosigncookie')
    if 'ais_url' in server:
        return ('plainpassword',)
    return ('demo',)


def create_client(settings, server, params):
    if params['type'] not in get_login_types(settings, server):
        raise ValueError("Unsupported login type")

    # Do the cosign login if required.
    if 'cosign' in server:
        cookies = get_cosign_cookies(settings, server, params)
    else:
        cookies = {}

    # TODO: Refactor Context arguments for REST and demo.
    ctx = Context(server.get('ais_url'), cookies)

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

    # Create the fladgejt client.
    # TODO: Other client types, depending on keys present in server.
    client = WebuiClient(ctx)

    return client
