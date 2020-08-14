
from fladgejt.rest import RestClient
from fladgejt.webui import WebuiClient


class HybridClient(RestClient, WebuiClient):
    def check_connection(self):
        RestClient.check_connection(self)
        WebuiClient.check_connection(self)

    def logout(self, ais_logout_suffix):
        RestClient.logout(self, ais_logout_suffix)
        WebuiClient.logout(self, ais_logout_suffix)
