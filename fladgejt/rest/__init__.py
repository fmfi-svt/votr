
from fladgejt.base import BaseClient
from .studium import RestStudiumMixin
#from .terminy import RestTerminyMixin


# Disable RestTerminyMixin until it gives us all columns.


class RestClient(RestStudiumMixin, BaseClient):
    def check_connection(self):
        self.context.request_json('')
        super().check_connection()
