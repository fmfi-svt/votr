
import os
import sys
from markupsafe import escape
from pathlib import Path
from urllib.parse import parse_qs, urlencode
from werkzeug.exceptions import HTTPException, MisdirectedRequest
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.routing import Map
from werkzeug.wrappers import Request, Response

from . import login, front, rpc, serve, cron, logutil, report
site_modules = [login, front, rpc, serve, cron, logutil, report]

class VotrApp(object):
    '''The main WSGI application class.'''

    def __init__(self, settings):
        self.settings = settings

        self.var = Path(__file__).resolve().parent.parent / settings.var_path

        self.saml_settings = login.build_saml_settings(settings, self.var)

        self.commands = {}
        for module in site_modules:
            if hasattr(module, 'commands'):
                self.commands.update(module.commands)

        self.url_map = Map()
        for module in site_modules:
            if hasattr(module, 'get_routes'):
                for rulefactory in module.get_routes():
                    self.url_map.add(rulefactory)

    def run_help(self, *args):
        '''Shows the usage when console.py is run with an unknown command.'''
        print('usage:')
        for module in site_modules:
            if hasattr(module, 'commands'):
                for command in module.commands.values():
                    if hasattr(command, 'help'):
                        print(command.help.replace('$0', sys.argv[0]))

    def run_command(self, args):
        '''Used by console.py to run the command given in `args`.'''
        command = args[0] if args else None
        handler = self.commands.get(command, self.run_help)
        return handler(self, *args[1:])

    def dispatch_request(self, request):
        '''Processes the HTTP request and returns a werkzeug `Response`.'''
        try:
            if self.settings.root_url and request.root_url != self.settings.root_url:
                raise MisdirectedRequest(f'Expected {self.settings.root_url} instead of {request.root_url}')

            endpoint, values = request.url_adapter.match()
            return endpoint(request, **values)
        except HTTPException as e:
            link = '<p><a href="%s">Back to main page</a></p>' % escape(self.settings.root_url or request.root_url)
            orig_get_body = e.get_body
            e.get_body = lambda environ, scope: orig_get_body(environ, scope) + link
            return e

    @Request.application
    def __call__(self, request):
        '''Main WSGI entry point.'''
        request.app = self

        request.max_content_length = 16 * 1024 * 1024
        request.max_form_memory_size = 2 * 1024 * 1024

        request.url_adapter = self.url_map.bind_to_environ(request.environ)

        cookie_prefix = '__Host-' if request.is_secure else ''
        cookie_name = f'{cookie_prefix}{self.settings.instance_id}_csession'
        cookie_str = request.cookies.get(cookie_name)
        try:
            cookie_dict = parse_qs(cookie_str or '', keep_blank_values=True)
            cookie_dict = { k: v[0] for k, v in cookie_dict.items() }
        except Exception:
            cookie_dict = {}
        cookie_dict_copy = cookie_dict.copy()
        request.votr_cookie_value = cookie_dict

        response = self.dispatch_request(request)

        if (request.votr_cookie_value is not cookie_dict or
            request.votr_cookie_value != cookie_dict_copy
        ):
            if not isinstance(response, Response):
                raise Exception('response is not a werkzeug.wrappers.Response')
            if request.votr_cookie_value:
                response.set_cookie(
                    cookie_name, urlencode(request.votr_cookie_value), path='/',
                    secure=request.is_secure, httponly=True, samesite='Lax')
            else:
                response.delete_cookie(
                    cookie_name, path='/',
                    secure=request.is_secure, httponly=True, samesite='Lax')

        return response

    @staticmethod
    def wrap_static(app):
        '''Adds a "/static" route for static files.

        This should only be used for the development server. Production servers
        should expose the /static directory directly.
        '''
        return SharedDataMiddleware(app, {
            '/static': os.path.join(os.path.dirname(__file__), 'static')
        })
