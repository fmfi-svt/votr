
from fladgejt.structures import Termin, Prihlasena_osoba
from aisikl.exceptions import RESTNotFoundError
from .studium import RestStudiumMixin


class RestTerminyMixin:
    def get_vypisane_terminy(
            self,
            studijny_program_skratka,
            zaciatok_studia,
            akademicky_rok):
        zl_id = RestStudiumMixin.get_zapisny_list_id(
            self,
            studijny_program_skratka,
            zaciatok_studia,
            akademicky_rok)

        predmety = self.context.request_json(
            "/zapisnyList/{}/predmety/".format(zl_id))

        result = []

        for predmet in predmety:
            terminy = self.context.request_json(
                "/terminyHodnotenia/predmetZapisnyList/{}/".format(predmet['id']))

            for termin in terminy:
                result.append(
                    Termin(
                        datum=termin['dat'],
                        cas=termin['cas'],
                        miestnost=termin['miestnosti'],
                        maximalne_prihlasenych=termin['maxPocet'],
                        hodnotiaci=termin['hodnotiaci'],
                        prihlasovanie_od=termin['prihlasovanie'],
                        prihlasovanie_do=termin['odhlasovanie'],
                        poznamka=termin['poznamka'],
                        moznost_prihlasit=termin['moznostPrihlasenia'],
                        pocet_prihlasenych=termin['pocetPrihlasenych']))

        return result

    def get_vypisane_terminy_predmetu(
            self,
            studijny_program_skratka,
            zaciatok_studia,
            akademicky_rok,
            skratka_predmetu):
        p_id = RestStudiumMixin.get_predmet_id(
            self,
            studijny_program_skratka,
            zaciatok_studia,
            akademicky_rok,
            skratka_predmetu)

        result = []

        terminy = self.context.request_json(
            "/terminyHodnotenia/predmetZapisnyList/{}/".format(predmet['id']))

        for termin in terminy:
            result.append(
                Termin(
                    datum=termin['datum'],
                    cas=termin['cas'],
                    miestnost=termin['miestnost'],
                    maximalne_prihlasenych=termin['maximalne_prihlasenych'],
                    hodnotiaci=termin['hodnotiaci'],
                    prihlasovanie_od=termin['prihlasovanie_od'],
                    prihlasovanie_do=termin['prihlasovanie_do'],
                    poznamka=termin['poznamka'],
                    moznost_prihlasit=termin['moznost_prihlasit']))

        return result

    def get_prihlaseny_studenti(
            self,
            studijny_program_skratka,
            zaciatok_studia,
            akademicky_rok,
            skratka_predmetu,
            datum,
            cas,
            miestnost,
            hodnotiaci):
        t_id = self._get_termin_id(
            studijny_program_skratka,
            zaciatok_studia,
            akademicky_rok,
            skratka_predmetu,
            datum,
            cas,
            miestnost,
            hodnotiaci)

        zoznam_prihlasenych = self.context.request_json(
            "/terminyHodnotenia/{}/zoznamPrihlasenych/".format(t_id))

        result = [
            Prihlasena_osoba(
                skratka=prihlaseny['skratka'],
                datum_prihlasenia=prihlaseny['datumPrihlasenia'],
                plne_meno=prihlaseny['plneMeno'],
                rocnik=prihlaseny['rocnik']) for prihlaseny in zoznam_prihlasenych]

        return result

    def _get_termin_id(
            self,
            studijny_program_skratka,
            zaciatok_studia,
            akademicky_rok,
            skratka_predmetu,
            datum,
            cas,
            miestnost,
            hodnotiaci):
        p_id = RestStudiumMixin.get_predmet_id(
            self,
            studijny_program_skratka,
            zaciatok_studia,
            akademicky_rok,
            skratka_predmetu)

        terminy = self.context.request_json(
            "/terminyHodnotenia/predmetZapisnyList/{}/".format(p_id))

        for termin in terminy:
            if termin['cas'] == cas and termin['dat'] == datum and termin[
                    'miestnosti'] == miestnost and termin['hodnotiaci'] == hodnotiaci:
                return termin['idTerminHodnotenia']

        raise RESTNotFoundError("Termin does not exists.")
