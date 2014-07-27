from fladgejt.demo.db import studia, zapisneListy, predmety, hodnotenia


class DemoStudiumMixin(object):
    def get_studia(self):
        return studia.get_studia()

    def get_zapisne_listy(self, studium_id):
        return zapisneListy.get_zapisneListy(studium_id)

    def get_prehlad_kreditov(self, studium_id):

        vsetky_hodnotenia = hodnotenia.get_hodnotenia()

        result = []

        for zapisnyList in self.get_zapisne_listy(studium_id):
            for predmet in predmety.get_predmety(zapisneListy.id):
                for hodnotenie in vsetky_hodnotenia:
                    if predmet.skratka == hodnotenie.skratka \
                       and zapisnyList.akademicky_rok == hodnotenie.akademicky_rok:
                        result.append(hodnotenie)

        return result
