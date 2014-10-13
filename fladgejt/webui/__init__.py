
from .hodnotenia import WebuiHodnoteniaMixin
from .predmety import WebuiPredmetyMixin
from .studium import WebuiStudiumMixin
from .terminy import WebuiTerminyMixin
from .obdobia import WebuiObdobiaMixin
from .uzivatel import WebuiUzivatelMixin


class WebuiClient(WebuiHodnoteniaMixin, WebuiPredmetyMixin, WebuiStudiumMixin,
                  WebuiTerminyMixin, WebuiObdobiaMixin, WebuiUzivatelMixin):
    def __init__(self, context):
        self.context = context

    def check_connection(self):
        soup = self.context.request_html('/ais/portal/changeTab.do?tab=0')
        username_element = soup.find(class_='user-name')
        if not (username_element and username_element.get_text()):
            raise Exception('AIS login expired.')

    def logout(self):
        self.context.request_html('/ais/logout.do')
