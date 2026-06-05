import os
import subprocess
from werkzeug.serving import run_simple
from votrfront.base import var_path


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

    os.makedirs(var_path('locks'), exist_ok=True)
    os.makedirs(var_path('logs'), exist_ok=True)
    os.makedirs(var_path('logdb'), exist_ok=True)
    os.makedirs(var_path('oldlogs'), exist_ok=True)
    os.makedirs(var_path('logarchive'), exist_ok=True)
    os.makedirs(var_path('sessions'), exist_ok=True)
    os.makedirs(var_path('reportlogs'), exist_ok=True)

    if https:
        ssl_context = (var_path('ssl.crt'), var_path('ssl.key'))
        if not os.path.exists(ssl_context[0]):
            subprocess.check_call([
                'openssl', 'req', '-x509', '-newkey', 'rsa:4096',
                '-keyout', 'ssl.key', '-out', 'ssl.crt',
                '-sha256', '-days', '365', '-nodes', '-subj', '/CN=*',
            ], cwd=var_path())
    else:
        ssl_context = None

    app_with_static = type(app).wrap_static(app)
    run_simple(bind, port, app_with_static, ssl_context=ssl_context,
               use_debugger=debug, use_reloader=True, threaded=True)


commands = {
    'serve': serve,
}
