
import os
from werkzeug.serving import run_simple


def serve(app, *args):
    if list(args) == ['--debug']:
        debug = True
    elif list(args) == []:
        debug = False
    else:
        raise ValueError('wrong args')

    os.makedirs(app.var_path('logs'), exist_ok=True)
    os.makedirs(app.var_path('logdb'), exist_ok=True)
    os.makedirs(app.var_path('oldlogs'), exist_ok=True)
    os.makedirs(app.var_path('logarchive'), exist_ok=True)
    os.makedirs(app.var_path('sessions'), exist_ok=True)

    app.wrap_static()
    run_simple('127.0.0.1', int(os.getenv('PORT') or 5000), app,
               use_debugger=debug, use_reloader=True, threaded=True)

serve.help = '  $0 serve [--debug]'


commands = {
    'serve': serve,
}
