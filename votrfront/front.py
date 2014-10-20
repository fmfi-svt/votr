
import os
import json
import traceback
from werkzeug.routing import Rule
from werkzeug.wrappers import Response
from . import sessions


template = '''
<!DOCTYPE html>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Votr</title>
<link rel="stylesheet" type="text/css" href="static/build/style.css">
<div id="votr"></div>
<noscript>JavaScript required.</noscript>
<script>/*INSERT*/</script>
'''.lstrip()
# TODO: add some nice noscript content for search engines etc.

build_path = os.path.join(os.path.dirname(__file__), 'static/build/')


def app_response(request, **my_data):
    my_data['url_root'] = request.url_root
    my_data['instance_name'] = request.app.settings.instance_name
    if 'csrf_token' not in my_data:
        my_data['servers'] = request.app.settings.servers

    if not os.path.exists(build_path + 'ok'):
        return Response('buildstatic failed!', status=500)

    is_debug = request.cookies.get('votr_debug')
    with open(build_path + ('jsdeps-dev' if is_debug else 'jsdeps-prod')) as f:
        scripts = f.read().split()

    content = template.replace('/*INSERT*/',
        'Votr = ' + json.dumps({ 'settings': my_data }).replace('</', '<\\/'))
    for script in scripts:
        content += '<script src="static/build/{}"></script>\n'.format(script)
    return Response(content, content_type='text/html; charset=UTF-8')


def front(request):
    csrf_token = None
    connection_error = None

    # If the user has no session cookie, just show the login form.
    if not sessions.get_cookie(request):
        return app_response(request)

    try:
        with sessions.logged_transaction(request) as session:
            csrf_token = session['csrf_token']
            session['client'].check_connection()
    except Exception:
        connection_error = traceback.format_exc()

    # If we can't open the session at all, show the login form, but complain.
    if not csrf_token:
        return app_response(request, invalid_session=True)

    # If the session is real but check_connection() failed, complain.
    if connection_error:
        return app_response(request,
            csrf_token=csrf_token, error=connection_error)

    # Otherwise, everything works and we can open the app.
    return app_response(request, csrf_token=csrf_token)


def die(request):
    # allows easy access to debugger on /500 if it's enabled.
    raise Exception()


def get_routes():
    yield Rule('/', methods=['GET'], endpoint=front)
    yield Rule('/500', endpoint=die)
