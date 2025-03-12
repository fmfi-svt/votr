
from aisikl.app import check_connection
from fladgejt.base import BaseClient
from .commonui import WebuiCommonUIMixin
from .hodnotenia import WebuiHodnoteniaMixin
from .obdobia import WebuiObdobiaMixin
from .osoby import WebuiOsobyMixin
from .pool import Pool
from .predmety import WebuiPredmetyMixin
from .studium import WebuiStudiumMixin
from .terminy import WebuiTerminyMixin
from .zapis import WebuiZapisMixin


class WebuiClient(WebuiCommonUIMixin, WebuiHodnoteniaMixin, WebuiObdobiaMixin,
                  WebuiOsobyMixin, WebuiPredmetyMixin, WebuiStudiumMixin,
                  WebuiTerminyMixin, WebuiZapisMixin, BaseClient):
    def __init__(self, context, *, logout_mode=None):
        super().__init__(context)
        self.app_pool = Pool(context)
        self.logout_mode = logout_mode or self.LOGOUT_NOTHING

    def check_connection(self):
        check_connection(self.context)
        super().check_connection()

    def prepare_for_rpc(self):
        self.app_pool.prepare_for_rpc(self.last_rpc_failed)
        super().prepare_for_rpc()

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
        super().logout()

    LOGOUT_WITH_REDIRECTS = "LOGOUT_WITH_REDIRECTS"
    LOGOUT_WITHOUT_REDIRECTS = "LOGOUT_WITHOUT_REDIRECTS"
    LOGOUT_NOTHING = "LOGOUT_NOTHING"
