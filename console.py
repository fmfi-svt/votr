#!/usr/bin/env python

try:
    import votrfront.local_settings as settings
    from votrfront.app import VotrApp
    from votrfront.proxied import ProxiedMiddleware

    application = VotrApp(settings=settings)
    proxied_application = ProxiedMiddleware(application)
    staticized_application = VotrApp.wrap_static(application)
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

f'{''}'  # Python >= 3.12 is required
