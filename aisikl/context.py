
from bs4 import BeautifulSoup
import json
import requests
from urllib.parse import urljoin
from .exceptions import RESTServerError


class Context:

    '''Context contains the things we need to store about an AIS session. When
    one user makes multiple Votr requests, they have the same Context. It
    contains our AIS cookie jar, and will later also include the open AIS
    applications and the Votr logs. (Most of Votr's logging will probably be
    per-session instead of per-request, because a Votr request can heavily
    depend on the previous ones.)

    Arguments:
        base_url: The server to connect to, e.g. "https://ais2.uniba.sk/".
        cookies: A dictionary of initial cookies.
    '''

    # TODO: Make sure this class is pickle-able.

    def __init__(self, base_url, cookies):
        self.base_url = base_url

        self.connection = requests.Session()
        for key in cookies:
            self.connection.cookies.set(key, cookies[key])

    def request_html(self, url, *, method='GET', **kwargs):
        '''Sends a request to AIS and parses the response as HTML.

        :param url: the URL, either absolute or relative to the AIS server.
        :param method: HTTP method for the request.
        :param \*\*kwargs: arguments for :meth:`requests.Session.request`.
        :return: a :class:`~BeautifulSoup` object.
        '''
        url = urljoin(self.base_url, url)
        response = self.connection.request(method, url, **kwargs)
        response.raise_for_status()
        return BeautifulSoup(response.text)

    def request_json(self, url, *, method='GET', **kwargs):
        '''Sends a request to REST API and parses the response as JSON.

        :param url: the URL, either absolute or relative to the AIS server.
        :param method: HTTP method for the request.
        :param \*\*kwargs: arguments for :meth:`requests.Session.request`.
        :return: a dictionary.
        '''
        url = urljoin(self.base_url, url)
        response = self.connection.request(method, url, verify=False, **kwargs)
        response.raise_for_status()

        response = json.loads(response.text)

        if response['status'] != 'OK':
            raise RESTServerError(
                "Status: {} Error:{}".format(
                    response['status'],
                    response['error']))

        return response['response']

    def log(self, type, message, data=None):
        '''Logs a message.

        Args:
            type: String used to group similar messages together.
            message: The log message. Should be a single line.
            data: A JSON-serializable object containing more details.
        '''
        # For now, just print it.
        print('\033[1;36m{} \033[1;33m{} \033[0m{}'.format(
            type, message, '' if data is None else json.dumps(data)))
