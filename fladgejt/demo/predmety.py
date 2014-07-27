from fladgejt.demo.db import studia, zapisneListy, predmety, hodnotenia


class DemoPredmetyMixin(object):
    def get_predmety(self, studium_id):
        return studia.get_studia()
