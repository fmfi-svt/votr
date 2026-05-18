import base64
import datetime
import os
import json
import traceback
import trio
from markupsafe import Markup
from starlette.responses import HTMLResponse, PlainTextResponse
from starlette.routing import Route
from votrfront import sessions
from votrfront.utils import check_header


template = Markup('''\
<!DOCTYPE html>
<html lang="sk">
<head>
<meta charset="UTF-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s</title>
<link rel="stylesheet" type="text/css" href="%(css)s">
<meta name="description" content="Votr ponúka študentom jednoduchší a \
pohodlnejší spôsob, ako robiť najčastejšie činnosti zo systému AIS. Zapíšte \
sa na skúšky, prezrite si vaše hodnotenia a skontrolujte si počet kreditov \
bez zbytočného klikania.">
%(analytics)s\
</head>
<body>
<span id="votr"></span>
<noscript>
<div class="v-common-centered-message">
<h1>Votr</h1>
<p><strong>Votr</strong> ponúka študentom jednoduchší a pohodlnejší spôsob, \
ako robiť najčastejšie činnosti zo systému AIS. Zapíšte sa na skúšky, prezrite \
si vaše hodnotenia a skontrolujte si počet kreditov bez zbytočného klikania.</p>
<p><strong>Votr na svoju správnu funkciu potrebuje zapnutý \
JavaScript.</strong></p>
</div>
</noscript>
<script nonce="%(nonce)s">Votr = %(init_json)s</script>
%(scripts)s
</body>
</html>
''')

analytics_template = Markup('''\
<script nonce="%(nonce)s">
(function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
(i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
})(window,document,'script','//www.google-analytics.com/analytics.js','ga');

ga('create', '%(ua_code)s', 'auto');
</script>
''')

static_path = os.path.join(os.path.dirname(__file__), 'static/')


def static_url(filename):
    mtime = int(os.path.getmtime(static_path + filename))
    return f'static/{filename}?v={mtime}'


def process_server(server):
    keep = ['title', 'login_types', 'ais_url', 'ais_cookie',
            'rest_url', 'rest_cookie']
    js_server = { k: server[k] for k in keep if k in server }
    if 'flashbacks_dir' in server and os.path.isdir(server['flashbacks_dir']):
        js_server['flashback_files'] = sorted(os.listdir(server['flashbacks_dir']))
    return js_server


async def app_response(request, **my_data):
    settings = request.state['settings']
    url_root = str(request.base_url)
    instance_id = settings.instance_id

    my_data['url_root'] = url_root
    my_data['instance_id'] = instance_id
    my_data['instance_title'] = settings.instance_title
    my_data['announcement_html'] = settings.announcement_html
    my_data['feedback_link'] = settings.feedback_link

    if settings.anketa_season and settings.anketa_end_ymd:
        my_data['anketa_season'] = settings.anketa_season
        dt = datetime.datetime(*settings.anketa_end_ymd)
        my_data['anketa_end_msec'] = int(dt.timestamp() * 1000)

    if 'csrf_token' not in my_data:
        my_data['servers'] = [process_server(s) for s in settings.servers]

    for i in range(30 * 10):
        try:
            with open(static_path + 'status') as f:
                status = f.read().strip()
        except FileNotFoundError:
            return PlainTextResponse('Missing static files.', status_code=500)
        if status != 'busy':
            break
        await trio.sleep(0.1)
    else:
        return PlainTextResponse(
            'Timed out waiting for webpack.', status_code=500)

    debug = request.cookies.get(instance_id + '_jsdev')
    if status == 'failed':
        return PlainTextResponse('Webpack build failed.', status_code=500)
    elif status == 'ok_dev' or (status == 'ok_both' and debug):
        scripts = ['prologue.dev.js', 'votr.dev.js', 'vendors_votr.dev.js']
    elif status == 'ok_prod' or (status == 'ok_both' and not debug):
        scripts = ['prologue.min.js', 'votr.min.js', 'vendors_votr.min.js']
    else:
        return PlainTextResponse('Unexpected webpack status.', status_code=500)

    my_data['both_js'] = status == 'ok_both'

    nonce = base64.b64encode(os.urandom(18)).decode('ascii')

    content = template % dict(
        nonce=nonce,
        title=settings.instance_title,
        init_json=Markup(json.dumps({ 'settings': my_data }).replace('</', '<\\/')),
        css=static_url('style.css'),
        scripts=Markup('\n').join(
            Markup('<script nonce="{}" src="{}"></script>').format(
                nonce, static_url(script))
            for script in scripts),
        analytics=(
            '' if not settings.ua_code else
            analytics_template % dict(nonce=nonce, ua_code=settings.ua_code)),
    )

    return HTMLResponse(content,
        headers={
            # no-store == force refresh even after pressing the back button.
            # http://blog.55minutes.com/2011/10/how-to-defeat-the-browser-back-button-cache/
            'Cache-Control': 'no-cache, max-age=0, must-revalidate, no-store',

            # based on https://csp.withgoogle.com/docs/strict-csp.html
            # object-src 'self' - they say 'none' may block Chrome's PDF reader.
            # TODO: Revisit object-src if http://crbug.com/271452 gets fixed.
            'Content-Security-Policy':
                "object-src 'self'; " +
                f"script-src 'nonce-{nonce}' 'strict-dynamic' " +
                "'unsafe-inline' https: http: 'report-sample'; " +
                "base-uri 'none'; " +
                f"report-uri {url_root}report?type=csp; " +
                f"report-to csp_{instance_id}",

            'Report-To': json.dumps({
                'group': f'csp_{instance_id}',
                'max_age': 24 * 60 * 60,
                'endpoints': [{ 'url': f'{url_root}report?type=csp-rt' }],
            }),
        })


async def front(request):
    check_header(request, 'Sec-Fetch-Mode', { 'navigate' })
    check_header(request, 'Sec-Fetch-Dest', { 'document' })

    csrf_token = None
    fake_time_msec = None
    connection_error = None

    # If the user has no session cookie, or it does not contain a sessid, just
    # show the login form.
    if not sessions.get_sessid_from_cookie(request):
        return await app_response(request)

    try:
        async with sessions.logged_transaction(request) as session:
            log = session['client'].context.log
            try:
                await log('front', 'Front session check started',
                    str(request.url))
                csrf_token = session['csrf_token']
                fake_time_msec = session['client'].fake_time_msec
                await session['client'].check_connection()
            except BaseException as e:
                await log('front',
                    f'Front session check failed with {type(e).__name__}',
                    traceback.format_exc())
                raise
            await log('front', 'Front session check finished')
    except Exception:
        connection_error = traceback.format_exc()

    # If we can't open the session at all, show the login form, but complain.
    if not csrf_token:
        return await app_response(request, invalid_session=True)

    # If the session is real but check_connection() failed, complain.
    if connection_error:
        return await app_response(
            request,
            csrf_token=csrf_token,
            fake_time_msec=fake_time_msec,
            error=connection_error,
        )

    # Otherwise, everything works and we can open the app.
    return await app_response(
        request,
        csrf_token=csrf_token,
        fake_time_msec=fake_time_msec,
    )


routes = [
    Route('/', endpoint=front),
]
