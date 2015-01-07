
import subprocess
import os
import time
from . import logutil


def cron(app):
    logutil.process_logfiles(
        app, [app.var_path('logs', sessid)
              for sessid in os.listdir(app.var_path('logs'))])

    now = time.time()

    for sessid in os.listdir(app.var_path('sessions')):
        path = app.var_path('sessions', sessid)
        mtime = os.path.getmtime(path)
        if now - mtime > app.settings.session_max_age:
            os.unlink(path)

    for sessid in os.listdir(app.var_path('logs')):
        if os.path.exists(app.var_path('sessions', sessid)):
            continue

        path = app.var_path('logs', sessid)
        mtime = os.path.getmtime(path)
        if now - mtime > app.settings.log_max_age:
            newpath = app.var_path('oldlogs', sessid[0:2], sessid + '.gz')

            try:
                os.mkdir(os.path.dirname(newpath))
            except FileExistsError:
                pass

            with open(newpath, 'wb') as output:
                # this is slower than using python's gzip library, but
                # correctly preserves the original name, mtime etc.
                subprocess.check_call(['gzip', '-c', path], stdout=output)
            os.utime(newpath, (mtime, mtime))

            os.unlink(path)

cron.help = '  $0 cron'


commands = {
    'cron': cron,
}
