"""Utilities for IPython/Jupyter notebooks and one-off experimental scripts.

Usage example:

    from nbenv import *
    client = await create_client(ais, get_login_params())
    app = await client._open_administracia_studia()
    ...

More information: https://github.com/fmfi-svt/votr/wiki/Praca-s-ipythonom-(sk)
"""

# Convenience imports.
import aisikl.portal  # noqa: F401 # pyright: ignore [reportUnusedImport]
from aisikl.app import Application as Application
from aisikl.operations import AbortBoxOp as AbortBoxOp
from aisikl.operations import CalendarBoxOp as CalendarBoxOp
from aisikl.operations import CloseApplicationOp as CloseApplicationOp
from aisikl.operations import CloseDialogOp as CloseDialogOp
from aisikl.operations import ConfirmBoxOp as ConfirmBoxOp
from aisikl.operations import EditDocOp as EditDocOp
from aisikl.operations import FileUploadOp as FileUploadOp
from aisikl.operations import FileXUploadOp as FileXUploadOp
from aisikl.operations import MessageBoxOp as MessageBoxOp
from aisikl.operations import OpenDialogOp as OpenDialogOp
from aisikl.operations import Operation as Operation
from aisikl.operations import Operations as Operations
from aisikl.operations import RefreshDialogOp as RefreshDialogOp
from aisikl.operations import ServerCloseApplicationOp as ServerCloseApplicationOp
from aisikl.operations import ShellExecOp as ShellExecOp
from aisikl.operations import ShowHelpOp as ShowHelpOp
from aisikl.operations import StartAppOp as StartAppOp
from fladgejt.login import create_client as create_client

# Internal imports.
from votrfront.default_settings import servers as _ds

# Servers. Choose one as the first argument of create_client().
default_servers = {_s.get("title"): _s for _s in _ds}
ais = default_servers["ais2.uniba.sk"]
ais_beta = default_servers["ais2-beta.uniba.sk"]
ais_test = default_servers["ais2-test.uniba.sk"]


def get_login_params() -> object:
    import getpass
    import json
    import os
    import tempfile

    filename = os.path.join(
        tempfile.gettempdir(), "votrlogin-" + getpass.getuser())

    if os.path.exists(filename):
        with open(filename) as f:
            return json.load(f)

    username = input("AIS username: ")
    password = getpass.getpass("AIS password: ")
    params = dict(type="saml_password", username=username, password=password)

    fd = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with open(fd, "w") as f:
        json.dump(params, f)

    return params
