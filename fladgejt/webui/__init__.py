
from aisikl.app import check_connection
from .commonui import WebuiCommonUIMixin
from .hodnotenia import WebuiHodnoteniaMixin
from .obdobia import WebuiObdobiaMixin
from .osoby import WebuiOsobyMixin
from .predmety import WebuiPredmetyMixin
from .studium import WebuiStudiumMixin
from .terminy import WebuiTerminyMixin
from .zapis import WebuiZapisMixin


class WebuiClient(WebuiCommonUIMixin, WebuiHodnoteniaMixin, WebuiObdobiaMixin,
                  WebuiOsobyMixin, WebuiPredmetyMixin, WebuiStudiumMixin,
                  WebuiTerminyMixin, WebuiZapisMixin):
    def __init__(self, context):
        self.context = context

    def check_connection(self):
        check_connection(self.context)

    def logout(self):
        self.context.request_html('/ais/logout.do')
