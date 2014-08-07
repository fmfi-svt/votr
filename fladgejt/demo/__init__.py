
from .studium import DemoStudiumMixin
from .terminy import DemoTerminyMixin


class DemoClient(DemoStudiumMixin, DemoTerminyMixin):
    def __init__(self, context):
        self.context = context

        
