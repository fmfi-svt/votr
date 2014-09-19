
from .studium import RestStudiumMixin
from .terminy import RestTerminyMixin


class RestClient(RestStudiumMixin, RestTerminyMixin):
    def __init__(self, context):
        self.context = context

    def check_connection(self):
        self.context.request_json('/')

    def logout(self):
        pass
