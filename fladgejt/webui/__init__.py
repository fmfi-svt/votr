
from .hodnotenia import WebuiHodnoteniaMixin
from .predmety import WebuiPredmetyMixin
from .studium import WebuiStudiumMixin
from .terminy import WebuiTerminyMixin
from .obdobia import WebuiObdobiaMixin


class WebuiClient(WebuiHodnoteniaMixin, WebuiPredmetyMixin, WebuiStudiumMixin,
                  WebuiTerminyMixin, WebuiObdobiaMixin):
    def __init__(self, context):
        self.context = context
