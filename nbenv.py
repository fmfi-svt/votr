'''Utilities for IPython/Jupyter notebooks and one-off experimental scripts.

Usage example:

    from nbenv import *
    client = create_client(ais, get_login_params())
    app = client._open_administracia_studia()
    ...

More information: https://github.com/fmfi-svt/votr/wiki/Praca-s-ipythonom-(sk)
'''

# Convenience imports.
import aisikl.app
import aisikl.portal
from aisikl.app import Application, assert_ops
from fladgejt.login import create_client
from votrfront.default_settings import servers as default_servers

# Servers. Choose one as the first argument of create_client().
ais = default_servers[0]
ais_beta = default_servers[2]
ais_test = default_servers[4]

def get_login_params():
    import getpass
    import json
    import os
    import tempfile

    filename = os.path.join(
        tempfile.gettempdir(), 'votrlogin-' + getpass.getuser())

    if os.path.exists(filename):
        with open(filename) as f:
            return json.load(f)

    username = input('AIS username: ')
    password = getpass.getpass('AIS password: ')
    params = dict(type='saml_password', username=username, password=password)

    fd = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with open(fd, 'w') as f:
        json.dump(params, f)

    return params
