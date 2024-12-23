
from bs4 import BeautifulSoup
import sys
import time
import json
import requests
from urllib.parse import urljoin
from aisikl.exceptions import RESTServerError, LoggedOutError


#: Set this to True (either in the source code, or with ``import aisikl.context;
#: aisikl.context.print_logs = True``) in order to print all logs to stderr.
print_logs = False


class Context:
    '''The common context for an AIS session. When one user opens multiple AIS
    applications, they share the same Context. It manages the HTTP cookie jar,
    performs HTTP requests and deals with logs.

    Arguments:
        ais_url: The AIS server to connect to, e.g. "https://ais2.uniba.sk/".
        rest_url: The REST server to connect to.
        dns_overrides: A dict[str, str] of hostname replacements. When sending
            any https request to K, the socket will connect() to V instead. The
            SNI name and Host header will still be K.
        logger: An optional :class:`Logger` instance to use.
    '''

    def __init__(self, *, ais_url=None, rest_url=None, dns_overrides=None,
                 logger=None):
        self.ais_url = ais_url
        self.rest_url = rest_url
        self.logger = logger or Logger()
        self.requests_session = requests.Session()
        if dns_overrides:
            for old_hostname, new_hostname in dns_overrides.items():
                self.requests_session.mount(
                    f'https://{old_hostname}/',
                    _DnsOverrideAdapter(old_hostname, new_hostname))

    def request_ais(self, url, *, method='GET', **kwargs):
        '''Sends a request to AIS and returns the :class:`requests.Response`.

        :param url: the URL, either absolute or relative to the AIS server.
        :param method: HTTP method for the request.
        :param \*\*kwargs: arguments for :meth:`requests.Session.request`.
        :return: a :class:`requests.Response` object.
        '''
        self.log('benchmark', 'Begin AIS network request')
        self.log('http', 'Requesting {} {}'.format(
            method, url.partition('?')[0]), [url, kwargs.get('data', None)])
        url = urljoin(self.ais_url, url)
        response = self.requests_session.request(method, url, **kwargs)
        response.raise_for_status()
        if response.headers.get('content-type', '').startswith('text'):
            self.log('http', 'Received response', response.text)
        else:
            self.log('http', 'Received response (binary data)')
        self.log('benchmark', 'End AIS network request')
        return response

    def request_html(self, url, *, method='GET', **kwargs):
        '''Sends a request to AIS and parses the response as HTML.

        :param url: the URL, either absolute or relative to the AIS server.
        :param method: HTTP method for the request.
        :param \*\*kwargs: arguments for :meth:`requests.Session.request`.
        :return: a ``BeautifulSoup`` object.
        '''
        return self.parse_html(self.request_ais(url, method=method, **kwargs))

    def parse_html(self, response):
        self.log('benchmark', 'Begin HTML parsing')
        soup = BeautifulSoup(response.text, 'lxml')
        self.log('benchmark', 'End HTML parsing')
        return soup

    def request_json(self, url, **data):
        '''Sends a request to REST API and parses the response as JSON.

        :param url: the URL, either absolute or relative to the AIS server.
        :param method: HTTP method for the request.
        :param \*\*kwargs: arguments for :meth:`requests.Session.request`.
        :return: a dictionary.
        '''
        self.log('benchmark', 'Begin REST network request')
        self.log('http', 'Requesting POST {}'.format(
            url.partition('?')[0]), [url, data])
        url = urljoin(self.rest_url, url)
        response = self.requests_session.request("POST", url, data=data)
        response.raise_for_status()
        self.log('http', 'Received response', response.text)
        self.log('benchmark', 'End REST network request')

        if not response.url.startswith(self.rest_url):
            raise LoggedOutError('REST login expired.')
        response = json.loads(response.text)

        if response['status'] != 'OK':
            raise RESTServerError(
                "Status: {status} Error: {error}".format(**response))

        self.log('http', 'Parsed JSON data')
        return response['response']

    def log(self, type, message, data=None):
        '''Logs a message.

        Args:
            type: String used to group similar messages together.
            message: The log message. Should be a single line.
            data: A JSON-serializable object containing more details.
        '''
        self.logger.log(type, message, data)


class Logger:
    '''Logs messages to various destinations.'''

    #: An open file to write log entries to. Votrfront sets it to a per-session
    #: log file on every request. The value is not preserved between requests.
    log_file = None

    #: A function that will be called with (timestamp, type, message, data) for
    #: every log entry. Votrfront uses it to send JSON logs to the client during
    #: a RPC request. The value is not preserved between requests.
    send_log = None

    def __getstate__(self):
        return {}

    def log(self, type, message, data=None):
        timestamp = time.time()

        if self.log_file and type != 'benchmark':
            # 'benchmark' is excluded from log files. It's too verbose.
            self.log_file.write(json.dumps([timestamp, type, message, data],
                                           ensure_ascii=False) + '\n')

        if self.send_log:
            self.send_log(timestamp, type, message, data)

        if print_logs:
            print('\033[1;36m{} \033[1;33m{} \033[0m{}'.format(
                type, message, '' if data is None else json.dumps(data)),
                file=sys.stderr)
    log.__doc__ = Context.log.__doc__


class _DnsOverrideAdapter(requests.adapters.HTTPAdapter):
    '''A HTTPAdapter which overrides the DNS resolution (i.e. the socket
    connect() address) from old_hostname to new_hostname.'''

    def __init__(self, old_hostname, new_hostname):
        super().__init__()
        self.old_hostname = old_hostname
        self.new_hostname = new_hostname

    def build_connection_pool_key_attributes(self, *args, **kwargs):
        host_params, pool_kwargs = (
            super().build_connection_pool_key_attributes(*args, **kwargs))
        if host_params['host'] != self.old_hostname:
            raise Exception(f'{host_params["host"]!r} != {self.old_hostname!r}')
        # Modifying this field changes the connect() address, SNI, expected cert
        # SAN, and default Host header. We only want to change the connect()
        # address, so we must change the rest back to old_hostname.
        host_params = { **host_params, 'host': self.new_hostname }
        # Change SNI and expected cert SAN back to old_hostname.
        pool_kwargs = { **pool_kwargs, 'server_hostname': self.old_hostname }
        return host_params, pool_kwargs

    def add_headers(self, request, **kwargs):
        # Explicitly set the Host header to old_hostname. FYI: It is usually
        # implicitly added by HTTPConnection.put_request() in http/client.py
        # using the value of HTTPConnection.host (not by requests or urllib3).
        if 'Host' in request.headers:
            raise Exception('Requests with custom Host header are unsupported')
        request.headers['Host'] = self.old_hostname

    def __getstate__(self):
        return {
            **super().__getstate__(),
            'old_hostname': self.old_hostname,
            'new_hostname': self.new_hostname,
        }


try:
    __IPYTHON__
except NameError:
    pass
else:
    from urllib.parse import quote
    from markupsafe import Markup
    from IPython.display import display, HTML

    def ipython_log(self, timestamp, type, message, data):
        if type == 'benchmark': return
        content = Markup('<span style="background:#FF8"><b>{}</b> {}</span>').format(type, message)
        if data is not None:
            if not isinstance(data, str):
                data = json.dumps(data)
            content = Markup('<details><summary>{}</summary><pre>{}</pre></details>').format(content, data)
        display(HTML(content))

    Logger.send_log = ipython_log
    # TODO: Do not use HTML logs when running command line ipython.
