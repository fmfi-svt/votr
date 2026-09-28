'''Utilities for IPython/Jupyter notebooks and one-off experimental scripts.

Usage example:

    from nbenv import *
    client = await create_client(ais, get_login_params())
    app = await client._open_administracia_studia()
    ...

More information: https://github.com/fmfi-svt/votr/wiki/Praca-s-ipythonom-(sk)
'''

# Convenience imports.
import aisikl.portal
from aisikl.app import Application
from fladgejt.login import create_client
from votrfront.default_settings import servers as _ds

# Servers. Choose one as the first argument of create_client().
default_servers = { _s['title']: _s for _s in _ds }
ais = default_servers['ais2.uniba.sk']
ais_beta = default_servers['ais2-beta.uniba.sk']
ais_test = default_servers['ais2-test.uniba.sk']

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
