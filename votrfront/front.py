
import os
import json
import traceback
from werkzeug.routing import Rule
from werkzeug.wrappers import Response
from . import sessions


template = '''
<!DOCTYPE html>
<html lang="sk">
<head>
<meta charset="UTF-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Votr</title>
<link rel="stylesheet" type="text/css" href="static/build/style.css">
%(analytics)s
</head>
<body>
<span id="votr"></span>
<noscript>
<div class="login-page">
<div class="login-content">
<h1>Votr</h1>
<p><strong>Votr</strong> ponúka študentom jednoduchší a pohodlnejší spôsob, ako
robiť najčastejšie činnosti zo systému AIS. Zapíšte sa na skúšky, prezrite si
vaše hodnotenia a skontrolujte si počet kreditov bez zbytočného klikania.</p>
<p><strong>Na používanie Votr musí byť zapnutý JavaScript.</strong></p>
</div>
</div>
</noscript>
<script>Votr = %(init_json)s</script>
%(scripts)s
</body>
</html>
'''.lstrip()

analytics_template = '''
<script>
(function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
(i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
})(window,document,'script','//www.google-analytics.com/analytics.js','ga');

ga('create', '%(ua_code)s', 'auto');
</script>
'''.strip()

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

    content = template % dict(
        init_json=json.dumps({ 'settings': my_data }).replace('</', '<\\/'),
        scripts='\n'.join(
            '<script src="static/build/{}"></script>'.format(script)
            for script in scripts),
        analytics=('' if not request.app.settings.ua_code else
            analytics_template % dict(ua_code=request.app.settings.ua_code)))

    return Response(content,
        content_type='text/html; charset=UTF-8',
        headers={
            # no-store == force refresh even after pressing the back button.
            # http://blog.55minutes.com/2011/10/how-to-defeat-the-browser-back-button-cache/
            'Cache-Control': 'no-cache, max-age=0, must-revalidate, no-store',
        })


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
