"""
Our current production server stack consists of Apache and Gunicorn. Apache uses
mod_cosign to handle SSO, and mod_proxy to forward HTTP requests to Gunicorn.
Gunicorn runs the Python code.

We used to run mod_wsgi, which made all Apache request variables directly
available in the WSGI environ. E.g. if mod_cosign sets COSIGN_SERVICE, the app
could just read environ['COSIGN_SERVICE']. But Gunicorn can't see the original
HTTP request or the internal variables set by other Apache modules. So we must
configure Apache to send everything we need to Gunicorn in additional request
headers. This middleware reads the headers and fills the WSGI environ like it
used to be with mod_wsgi.

It's the same idea as `werkzeug.middleware.proxy_fix.ProxyFix`, but using a
custom list of headers.
"""

import base64
import traceback
from werkzeug.exceptions import InternalServerError


class ProxiedMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        try:
            _fix_environ(environ)
            next_app = self.app
        except Exception:
            environ['wsgi.errors'].write(
                'ProxiedMiddleware error (environ=%r):\n%s' %
                    (environ, traceback.format_exc()))
            next_app = InternalServerError()

        return next_app(environ, start_response)


def _check(condition):
    if not condition: raise Exception('see stack trace')


def _fix_environ(environ):
    # To protect against https://github.com/benoitc/gunicorn/issues/2799, we
    # only use header names that don't contain "-" or "_". As an additional
    # precaution, we also check the header values don't contain any comma.

    # VotrRemoteAddr -> REMOTE_ADDR: Original IP address. Currently unused by
    # Votr. It's here just for feature parity with ProxyFix.
    ip = environ['HTTP_VOTRREMOTEADDR']
    _check(ip)
    _check(',' not in ip)
    environ['REMOTE_ADDR'] = ip

    # VotrRequestScheme -> wsgi.url_scheme: Original scheme. Used to generate
    # absolute links, e.g. for `request.url_root` in votrfront/front.py. Votr
    # always uses HTTPS in production, but let's check anyway.
    request_scheme = environ['HTTP_VOTRREQUESTSCHEME']
    _check(request_scheme == 'http' or request_scheme == 'https')
    environ['wsgi.url_scheme'] = request_scheme

    # VotrCosignService -> COSIGN_SERVICE: Name of the Cosign login cookie. Set
    # by mod_cosign. Read by votrfront/login.py. If logged out, the header is
    # empty and the WSGI environ should not have this key.
    cosign_service = environ['HTTP_VOTRCOSIGNSERVICE']
    _check(',' not in cosign_service)
    if cosign_service == '':
        environ.pop('COSIGN_SERVICE', None)
    else:
        environ['COSIGN_SERVICE'] = cosign_service

    # VotrRemoteUser -> REMOTE_USER: Logged in username. Set by mod_cosign.
    # Read by votrfront/login.py using the Request.remote_user property, and by
    # access_log_format in gunicorn.conf.py. If logged out, the header contains
    # "-" (to look nice in the access log) and the WSGI environ should not have
    # this key.
    remote_user = environ['HTTP_VOTRREMOTEUSER']
    _check(remote_user)
    _check(',' not in remote_user)
    if remote_user == '-':
        environ.pop('REMOTE_USER', None)
    else:
        environ['REMOTE_USER'] = remote_user

    # No need to deal with these environ keys:
    #
    # * HTTP_HOST: Apache with "ProxyPreserveHost On" forwards the original Host
    #   header just like we want. It even adds a Host if it's missing (using its
    #   ServerName). So we don't need X-Forwarded-Host or X-Forwarded-Port.
    #
    # * SERVER_NAME, SERVER_PORT: Werkzeug only reads them if HTTP_HOST is unset
    #   (see werkzeug/wsgi.py). So Gunicorn's value doesn't matter.
    #
    # * AUTH_TYPE, COSIGN_FACTOR, REMOTE_REALM, KRB5CCNAME: More variables set
    #   by mod_cosign. But these are mostly useless. See also:
    #   cosign-3.2.0/filters/apache2/mod_cosign.c
    #   http://webservices.itcs.umich.edu/mediawiki/cosign/index.php/cosign_wiki:CosignFilterSpec
    #
    # * CONTEXT_DOCUMENT_ROOT, CONTEXT_PREFIX, DOCUMENT_ROOT, GATEWAY_INTERFACE,
    #   PATH_TRANSLATED, REMOTE_PORT, REQUEST_URI, SCRIPT_FILENAME, SERVER_ADDR,
    #   SERVER_ADMIN, SERVER_SIGNATURE, SSL_TLS_SNI, apache.version, mod_wsgi.*,
    #   mod_wsgi.version, ...: the environ used to contain many other variables
    #   from Apache and mod_wsgi, but nothing in Votr or Werkzeug uses them.
