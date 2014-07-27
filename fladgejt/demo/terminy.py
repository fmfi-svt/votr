from collection import defaultdict
from fladgejt.structures import zapisneListy, predmety, terminy
from fladgejt.demo.db import get_aktualny_datetime, get_aktualna_prihlasena_osoba


class DemoTerminyMixin:
    def __init__(self):
        self.lokalne_prihlasene_terminy = None
        self.lokalne_vsetky_terminy = None
        self.lokalne_zoznam_prihlasenych = defaultdict(list)

    def get_predmety(self, studium_id):
        return [predmet
                for predmet in predmety.get_predmety(zapisneListy.id)
                for zapisnyList in zapisneListy.get_zapisne_listy(studium_id)]

    def _filter_terminy(self, studium_id, data):
        result = []

        for zapisnyList in self.get_zapisne_listy(studium_id):
            for predmet in predmety.get_predmety(zapisneListy.id):
                for termin in data:
                    if termin.predmet_id == predmet.id:
                        result.append(termin)

        return result

    def get_prihlasene_terminy(self, studium_id):
        if self.lokalne_prihlasene_terminy is None:
            self.lokalne_prihlasene_terminy = terminy.get_prihlasene_terminy()
        return self._filter_terminy(studium_id, self.lokalne_prihlasene_terminy)

    def get_vypisane_terminy(self, studium_id):
        if self.lokalne_vsetky_terminy is None:
            self.lokalne_vsetky_terminy = terminy.get_terminy()
        return self._filter_terminy(studium_id, self.lokalne_vsetky_terminy)

    def get_vypisane_terminy_predmetu(self, studium_id, predmet_id):
        return [termin
                for termin in self.get_vypisane_terminy(studium_id)
                if termin.predmet_id == predmet_id]

    def get_prihlaseny_studenti(self, studium_id, termin_id):
        if termin_id in self.lokalne_zoznam_prihlasenych.keys():
            self.lokalne_zoznam_prihlasenych[termin_id] = terminy.zoznam_prihlasenych(termin_id)
        return self.lokalne_zoznam_prihlasenych[termin_id]

    def odhlas_z_terminu(self, studium_id, termin_id):
        def _matches(a, b, keys):
            for k in keys:
                if a.k != b.k:
                    return False
            return True

        for i, termin in enumerate(self.get_prihlasene_terminy(studium_id)):
            if termin.id == termin_id:
                del self.lokalne_prihlasene_terminy[i]
                aktualna_osoba = get_aktualna_prihlasena_osoba()
                for i, prihlasena_osoba in enumerate(self.lokalne_zoznam_prihlasenych[termin_id]):
                    if _matches(prihlasena_osoba, aktualna_osoba, aktualna_osoba._asdict().keys):
                        del self.lokalne_zoznam_prihlasenych[termin_id][i]
                # TODO upravit spravny zaznam v self.lokalne_vsetky_terminy
                #self.lokalne_vsetky_terminy[???].pocet_prihlasenych -= 1
                #self.lokalne_vsetky_terminy[???].moznost_prihlasit = 'A'
                return True
        raise Exception('Termin id: {} nenajdeny.'.format(termin_id))
        # TODO dohodnut sa ake exception chcem hadzat.

    def prihlas_na_termin(self, studium_id, termin_id):
        for i, termin in enumerate(self.get_prihlasene_terminy(studium_id)):
            if termin.id == termin_id:
                raise Exception('Na termin id: {} ste už prihlásený.'.format(termin_id))

        for i, termin in enumerate(self.get_vypisane_terminy(studium_id)):
            if termin.id == termin_id and termin.moznost_prihlasit == 'A' \
               and termin.pocet_prihlasenych < termin.maximalne_prihlasenych \
               and termin.prihlasovanie_od <= get_aktualny_datetime() \
               and termin.prihlasovanie_do > get_aktualny_datetime():
                self.lokalne_prihlasene_terminy.append(termin)
                self.lokalne_vsetky_terminy[i].pocet_prihlasenych += 1
                if termin.pocet_prihlasenych == termin.maximalne_prihlasenych:
                    self.lokalne_vsetky_terminy[i].moznost_prihlasit = 'N'
                self.lokalne_zoznam_prihlasenych[termin_id].append(get_aktualna_prihlasena_osoba())

        raise Exception('Na termin id: {} sa nedá prihlásiť.'.format(termin_id))