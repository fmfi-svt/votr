
from .studium import RestStudiumMixin
from .terminy import RestTerminyMixin


class DemoClient(DemoStudiumMixin, DemoTerminyMixin):
    def __init__(self, context):
        self.context = context

        
