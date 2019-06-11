
import os
import json
import time
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
<link rel="stylesheet" type="text/css" href="%(css)s">
<link href="https://fonts.googleapis.com/css?family=Open+Sans:300,400,700&amp;subset=latin-ext" rel="stylesheet">
<meta name="description" content="Votr ponúka študentom jednoduchší a \
pohodlnejší spôsob, ako robiť najčastejšie činnosti zo systému AIS. Zapíšte \
sa na skúšky, prezrite si vaše hodnotenia a skontrolujte si počet kreditov \
bez zbytočného klikania.">
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

static_path = os.path.join(os.path.dirname(__file__), 'static/')


def static_url(filename):
    mtime = int(os.path.getmtime(static_path + filename))
    return 'static/{}?v={}'.format(filename, mtime)


def app_response(request, **my_data):
    my_data['url_root'] = request.url_root
    my_data['instance_name'] = request.app.settings.instance_name
    my_data['anketa_cookie_name'] = request.app.settings.anketa_cookie_name
    my_data['anketa_cookie_hide_date'] = request.app.settings.anketa_cookie_hide_date
    if 'csrf_token' not in my_data:
        my_data['servers'] = request.app.settings.servers

    for i in range(60):
        try:
            with open(static_path + 'status') as f:
                status = f.read().strip()
        except FileNotFoundError:
            return Response('Missing static files.', status=500)
        if status != 'busy':
            break
        time.sleep(0.1)
    else:
        return Response('Timed out waiting for webpack.', status=500)

    debug = request.cookies.get('votr_debug')
    if status == 'failed':
        return Response('Webpack build failed.', status=500)
    elif status == 'ok_dev' or (status == 'ok_both' and debug):
        scripts = ['prologue.dev.js', 'votr.dev.js', 'vendors_votr.dev.js']
    elif status == 'ok_prod' or (status == 'ok_both' and not debug):
        scripts = ['prologue.min.js', 'votr.min.js', 'vendors_votr.min.js']
    else:
        return Response('Unexpected webpack status.', status=500)

    content = template % dict(
        init_json=json.dumps({ 'settings': my_data }).replace('</', '<\\/'),
        css=static_url('style.css'),
        scripts='\n'.join(
            '<script src="{}"></script>'.format(static_url(script))
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
    if not sessions.get_session_cookie(request):
        return app_response(request)

    try:
        with sessions.logged_transaction(request) as session:
            log = session['client'].context.log
            try:
                log('front', 'Front session check started',
                    request.full_path)
                csrf_token = session['csrf_token']
                session['client'].check_connection()
            except Exception as e:
                log('front',
                    'Front session check failed with {}'.format(
                        type(e).__name__),
                    traceback.format_exc())
                raise
            log('front', 'Front session check finished')
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
