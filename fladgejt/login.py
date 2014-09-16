
import os
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
        raise NotImplementedError("cosignpassword not yet implemented")   # TODO

    if params['type'] == 'cosignproxy':
        # http://webapps.itcs.umich.edu/cosign/index.php/Using_Proxy_Cookies
        name, value = params['cosign_service']
        filename = name + '=' + value.partition('/')[0]
        result = {}
        with open(os.path.join(settings.cosign_proxy, filename)) as f:
            for line in f:
                # Remove starting "x" and everything after the space.
                name, _, value = line[1:].split()[0].partition('=')
                result[name] = value
        return result

    if params['type'] == 'cosigncookie':
        name = server['ais_cookie']
        value = parse_cookie_string(params['cookie'], name)
        return { name: value }

    return {}


def create_client(settings, server, params):
    if params['type'] not in server['login_types']:
        raise ValueError("Unsupported login type")

    # Do the cosign login if required.
    cookies = get_cosign_cookies(settings, server, params)

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
