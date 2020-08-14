
from .studium import RestStudiumMixin
from .terminy import RestTerminyMixin


# Disable RestTerminyMixin until it gives us all columns.
RestTerminyMixin = object


class RestClient(RestStudiumMixin, RestTerminyMixin):
    def __init__(self, context):
        self.context = context

    def check_connection(self):
        self.context.request_json('')

    def logout(self, ais_logout_suffix):
        pass
