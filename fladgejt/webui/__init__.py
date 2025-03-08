
from aisikl.app import check_connection
from .commonui import WebuiCommonUIMixin
from .hodnotenia import WebuiHodnoteniaMixin
from .obdobia import WebuiObdobiaMixin
from .osoby import WebuiOsobyMixin
from .predmety import WebuiPredmetyMixin
from .studium import WebuiStudiumMixin
from .terminy import WebuiTerminyMixin
from .zapis import WebuiZapisMixin
from .test_fladgejt import WebuiTestFladgejtMixin


class WebuiClient(WebuiCommonUIMixin, WebuiHodnoteniaMixin, WebuiObdobiaMixin,
                  WebuiOsobyMixin, WebuiPredmetyMixin, WebuiStudiumMixin,
                  WebuiTerminyMixin, WebuiZapisMixin, WebuiTestFladgejtMixin):
    def __init__(self, context):
        self.context = context

    def check_connection(self):
        check_connection(self.context)

    def logout(self):
        if self.logout_mode == self.LOGOUT_WITH_REDIRECTS:
            self.context.log('logout', 'Requesting logout.do with redirects')
            self.context.request_html('/ais/logout.do')
        elif self.logout_mode == self.LOGOUT_WITHOUT_REDIRECTS:
            self.context.log('logout', 'Requesting logout.do without redirects')
            self.context.request_html('/ais/logout.do', allow_redirects=False)
        elif self.logout_mode == self.LOGOUT_NOTHING:
            self.context.log('logout', 'Skipped logout.do')
        else:
            raise Exception("unknown logout_mode")

    LOGOUT_WITH_REDIRECTS = "LOGOUT_WITH_REDIRECTS"
    LOGOUT_WITHOUT_REDIRECTS = "LOGOUT_WITHOUT_REDIRECTS"
    LOGOUT_NOTHING = "LOGOUT_NOTHING"

    logout_mode = LOGOUT_NOTHING

    fake_time_msec = None
