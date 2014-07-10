
from .studium import RestStudiumMixin
from .terminy import RestTerminyMixin


class RestClient(RestStudiumMixin, RestTerminyMixin):
    def __init__(self, context):
        self.context = context
