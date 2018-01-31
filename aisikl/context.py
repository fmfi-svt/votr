
from bs4 import BeautifulSoup
import time
import json
import requests
from urllib.parse import urljoin
from aisikl.exceptions import RESTServerError, LoggedOutError


class Context:
    '''Context contains the things we need to store about an AIS session. When
    one user makes multiple Votr requests, they have the same Context. It
    contains our AIS cookie jar, and will later also include the open AIS
    applications and the Votr logs. (Most of Votr's logging will probably be
    per-session instead of per-request, because a Votr request can heavily
    depend on the previous ones.)

    Arguments:
        cookies: A dictionary of initial cookies.
        ais_url: The AIS server to connect to, e.g. "https://ais2.uniba.sk/".
        rest_url: The REST server to connect to

    Attributes:
        send_log: A function that will be called with (timestamp, type,
            message, data) for every log entry. Used to send JSON logs to the
            client during a RPC request.
        log_file: A file to write log entries to. Used when this Context is
            part of a votrfront session.
        print_logs: Set to True to print log entries to the console.
    '''

    # TODO: Make sure this class is pickle-able.

    def __init__(self, cookies, ais_url=None, rest_url=None):
        self.ais_url = ais_url
        self.rest_url = rest_url

        self.connection = requests.Session()
        for key in cookies:
            self.connection.cookies.set(key, cookies[key])

    def request_ais(self, url, *, method='GET', **kwargs):
        '''Sends a request to AIS and returns the :class:`requests.Response`.

        :param url: the URL, either absolute or relative to the AIS server.
        :param method: HTTP method for the request.
        :param \*\*kwargs: arguments for :meth:`requests.Session.request`.
        :return: a :class:`requests.Response` object.
        '''
        self.log('http', 'Requesting {} {}'.format(
            method, url.partition('?')[0]), [url, kwargs.get('data', None)])
        url = urljoin(self.ais_url, url)
        response = self.connection.request(method, url, **kwargs)
        response.raise_for_status()
        if response.headers.get('content-type', '').startswith('text'):
            self.log('http', 'Received response', response.text)
        else:
            self.log('http', 'Received response (binary data)')
        return response

    def request_html(self, url, *, method='GET', **kwargs):
        '''Sends a request to AIS and parses the response as HTML.

        :param url: the URL, either absolute or relative to the AIS server.
        :param method: HTTP method for the request.
        :param \*\*kwargs: arguments for :meth:`requests.Session.request`.
        :return: a ``BeautifulSoup`` object.
        '''
        response = self.request_ais(url, method=method, **kwargs)
        soup = BeautifulSoup(response.text, 'lxml')
        self.log('http', 'Parsed HTML data')
        return soup

    def request_json(self, url, **data):
        '''Sends a request to REST API and parses the response as JSON.

        :param url: the URL, either absolute or relative to the AIS server.
        :param method: HTTP method for the request.
        :param \*\*kwargs: arguments for :meth:`requests.Session.request`.
        :return: a dictionary.
        '''
        self.log('http', 'Requesting POST {}'.format(
            url.partition('?')[0]), [url, data])
        url = urljoin(self.rest_url, url)
        response = self.connection.request("POST", url, data=data)
        response.raise_for_status()
        self.log('http', 'Received response', response.text)

        if not response.url.startswith(self.rest_url):
            raise LoggedOutError('REST login expired.')
        response = json.loads(response.text)

        if response['status'] != 'OK':
            raise RESTServerError(
                "Status: {status} Error: {error}".format(**response))

        self.log('http', 'Parsed JSON data')
        return response['response']

    log_file = None
    send_log = None
    print_logs = False

    def log(self, type, message, data=None):
        '''Logs a message.

        Args:
            type: String used to group similar messages together.
            message: The log message. Should be a single line.
            data: A JSON-serializable object containing more details.
        '''
        timestamp = time.time()

        if self.log_file:
            self.log_file.write(json.dumps([timestamp, type, message, data],
                                           ensure_ascii=False) + '\n')

        if self.send_log:
            self.send_log(timestamp, type, message, data)
        elif self.print_logs:
            print('\033[1;36m{} \033[1;33m{} \033[0m{}'.format(
                type, message, '' if data is None else json.dumps(data)))


try:
    __IPYTHON__
except NameError:
    pass
else:
    from urllib.parse import quote
    from jinja2 import Markup
    from IPython.display import display, HTML

    def data_link(title, content):
        return Markup(' <a href="{}" target="_blank">{}</a>').format(
            'data:text/plain;charset=UTF-8,' + quote(content), title)

    def ipython_log(self, timestamp, type, message, data):
        parts = []
        parts.append(Markup('<span style="background:#FF8">'))
        parts.append(Markup('<b>{}</b> {}').format(type, message))
        if data is not None:
            parts.append(data_link('JSON', json.dumps(data)))
        if isinstance(data, str):
            parts.append(data_link('Plain', data))
        parts.append(Markup('</span>'))
        display(HTML(''.join(parts)))

    Context.send_log = ipython_log
    # TODO: Do not use HTML logs when running command line ipython.
