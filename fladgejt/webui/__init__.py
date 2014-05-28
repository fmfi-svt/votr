
from .hodnotenia import WebuiHodnoteniaMixin
from .predmety import WebuiPredmetyMixin
from .studium import WebuiStudiumMixin
from .terminy import WebuiTerminyMixin


class WebuiClient(WebuiHodnoteniaMixin, WebuiPredmetyMixin, WebuiStudiumMixin,
                  WebuiTerminyMixin):
    def __init__(self, context):
        self.context = context
