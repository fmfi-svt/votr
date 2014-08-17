#!/usr/bin/env python

try:
    import votrfront.local_settings as settings
except ImportError as e:
    if 'local_settings' not in str(e): raise
    import votrfront.default_settings as settings

from votrfront.app import VotrApp
application = VotrApp(settings=settings)

if __name__ == '__main__':
    import sys
    sys.exit(application.run_command(sys.argv[1:]))

# force a SyntaxError when using Python 2 by mistake
if False: print("you must use Python 3 to run this", end='')
