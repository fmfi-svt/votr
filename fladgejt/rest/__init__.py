
from .studium import RestStudiumMixin


class RestClient(RestStudiumMixin):
    def __init__(self, context):
        self.context = context
