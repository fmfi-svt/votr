
from fladgejt.rest import RestClient
from fladgejt.webui import WebuiClient


class HybridClient(RestClient, WebuiClient):
    def check_connection(self):
        RestClient.check_connection(self)
        WebuiClient.check_connection(self)

    def logout(self):
        RestClient.logout(self)
        WebuiClient.logout(self)
