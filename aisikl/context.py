
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin

class Context:
    '''Context contains the things we need to store about an AIS2 session. When
    one user makes multiple Votr requests, they have the same Context. It
    contains our AIS2 cookie jar, and will later also include the open AIS2
    applications and the Votr logs. (Most of Votr's logging will probably be
    per-session instead of per-request, because a Votr request can heavily
    depend on the previous ones.)

    :param base_url: the server to connect to, e.g. "https://ais2.uniba.sk/".
    :param cookies: A dictionary of initial cookies.
    '''

    # TODO: Make sure this class is pickle-able.

    def __init__(self, base_url, cookies):
        self.base_url = base_url

        self.connection = requests.Session()
        for key in cookies:
            self.connection.cookies.set(key, cookies[key])

    def request_html(self, url, *, method='GET', **kwargs):
        '''Sends a request to AIS2 and parses the response as HTML.

        :param url: the URL, either absolute or relative to the AIS2 server.
        :param method: HTTP method for the request.
        :param \*\*kwargs: arguments for :meth:`requests.Session.request`.
        :return: a :class:`~BeautifulSoup` object.
        '''
        url = urljoin(self.base_url, url)
        response = self.connection.request(method, url, **kwargs)
        response.raise_for_status()
        return BeautifulSoup(response.text)
