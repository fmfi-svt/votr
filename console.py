#!/usr/bin/env python

try:
    try:
        import votrfront.local_settings as settings
    except ImportError as e:
        if 'local_settings' not in str(e): raise
        import votrfront.default_settings as settings

    from votrfront.app import VotrApp
    from votrfront.proxied import ProxiedMiddleware

    application = VotrApp(settings=settings)
    proxied_application = ProxiedMiddleware(application)
except Exception:
    import os, sys, time, traceback
    if not (__name__ == '__main__' and os.getenv('WERKZEUG_RUN_MAIN')): raise
    traceback.print_exc()
    print(" * Initialization failed, trying again in 5 seconds")
    time.sleep(5)
    sys.exit(3)   # return code used by werkzeug to request a reload

if __name__ == '__main__':
    import sys
    sys.exit(application.run_command(sys.argv[1:]))

# force a SyntaxError when using Python 2 by mistake
if False: print("you must use Python 3 to run this", end='')
