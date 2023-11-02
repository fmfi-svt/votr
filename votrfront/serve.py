
import os
import subprocess
from werkzeug.serving import run_simple


def serve(app, *args):
    debug = False
    https = False
    port = 5000
    bind = '127.0.0.1'

    for arg in args:
        if arg == '--debug':
            debug = True
        elif arg == '--https':
            https = True
        elif arg.startswith('--port='):
            port = int(arg[7:])
        elif arg.startswith('--bind='):
            bind = arg[7:]
        else:
            raise Exception('Unexpected argument %r' % arg)

    os.makedirs(app.var / 'logs', exist_ok=True)
    os.makedirs(app.var / 'logdb', exist_ok=True)
    os.makedirs(app.var / 'oldlogs', exist_ok=True)
    os.makedirs(app.var / 'logarchive', exist_ok=True)
    os.makedirs(app.var / 'sessions', exist_ok=True)
    os.makedirs(app.var / 'reportlogs', exist_ok=True)

    if https:
        ssl_context = (app.var / 'ssl.crt', app.var / 'ssl.key')
        if not os.path.exists(ssl_context[0]):
            subprocess.check_call([
                'openssl', 'req', '-x509', '-newkey', 'rsa:4096',
                '-keyout', 'ssl.key', '-out', 'ssl.crt',
                '-sha256', '-days', '365', '-nodes', '-subj', '/CN=*',
            ], cwd=app.var)
    else:
        ssl_context = None

    app.wrap_static()
    run_simple(bind, port, app, ssl_context=ssl_context,
               use_debugger=debug, use_reloader=True, threaded=True)

serve.help = '  $0 serve [--debug] [--https] [--bind=X.X.X.X] [--port=N]'


commands = {
    'serve': serve,
}
