
from .hodnotenia import DemoHodnoteniaMixin
from .predmety import DemoPredmetyMixin
from .studium import DemoStudiumMixin
from .terminy import DemoTerminyMixin
from .obdobia import DemoObdobiaMixin
from .osoby import DemoOsobyMixin


class DemoClient(DemoHodnoteniaMixin, DemoPredmetyMixin, DemoStudiumMixin,
                 DemoTerminyMixin, DemoObdobiaMixin, DemoOsobyMixin):
    def __init__(self, context):
        self.context = context
        super().__init__()

    def check_connection(self):
        pass

    def logout(self):
        pass
