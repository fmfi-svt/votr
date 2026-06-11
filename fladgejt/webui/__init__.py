from aisikl.app import check_connection
from fladgejt.base import BaseClient
from fladgejt.webui.commonui import WebuiCommonUIMixin
from fladgejt.webui.hodnotenia import WebuiHodnoteniaMixin
from fladgejt.webui.obdobia import WebuiObdobiaMixin
from fladgejt.webui.osoby import WebuiOsobyMixin
from fladgejt.webui.pool import Pool
from fladgejt.webui.predmety import WebuiPredmetyMixin
from fladgejt.webui.studium import WebuiStudiumMixin
from fladgejt.webui.terminy import WebuiTerminyMixin
from fladgejt.webui.zapis import WebuiZapisMixin
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from aisikl.context import Context

class WebuiClient(WebuiHodnoteniaMixin, WebuiObdobiaMixin,
                  WebuiOsobyMixin, WebuiPredmetyMixin,
                  WebuiTerminyMixin, WebuiZapisMixin, WebuiStudiumMixin, WebuiCommonUIMixin, BaseClient):
    def __init__(self, context: Context, *, logout_mode: str | None=None) -> None:
        super().__init__(context)
        self.app_pool = Pool(context)
        self.logout_mode = logout_mode or self.LOGOUT_NOTHING

    @override
    def check_connection(self) -> None:
        check_connection(self.context)
        super().check_connection()

    @override
    def prepare_for_rpc(self) -> None:
        self.app_pool.prepare_for_rpc(self.last_rpc_failed)
        super().prepare_for_rpc()

    @override
    def logout(self) -> None:
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
