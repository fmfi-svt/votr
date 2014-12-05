# -*- coding: utf-8 -*-

from fladgejt.helpers import with_key_args
from fladgejt.structures import Predmet, Termin, PrihlasenyStudent
from .datumy import rok, datum, ak_rok


class DemoTerminyMixin:
    def __init__(self):
        super().__init__()
        self._terminy = [
            # TODO
        ]

    @with_key_args(True, True)
    def get_vidim_terminy_hodnotenia(self, studium_key, zapisny_list_key):
        return True
        # TODO: return False somewhere...

    @with_key_args(True, True)
    def get_predmety(self, studium_key, zapisny_list_key):
        result = [Predmet(skratka=hodnotenie.skratka,
                          nazov=hodnotenie.nazov,
                          typ_vyucby=hodnotenie.typ_vyucby,
                          semester=hodnotenie.semester,
                          kredit=hodnotenie.kredit)
                  for hodnotenie in self.get_hodnotenia(
                      studium_key, zapisny_list_key)]
        return result

    @with_key_args(True, True)
    def get_prihlasene_terminy(self, studium_key, zapisny_list_key):
        return []
        # TODO

    @with_key_args(True, True)
    def get_vypisane_terminy(self, studium_key, zapisny_list_key):
        result = []

        for predmet in self.get_predmety(studium_key, zapisny_list_key):
            result.extend(self.get_vypisane_terminy_predmetu(
                studium_key, zapisny_list_key, predmet.key))

        return result

    @with_key_args(True, True, True)
    def get_vypisane_terminy_predmetu(self, studium_key, zapisny_list_key, predmet_key):
        return []
        # TODO

    @with_key_args(True, True, True, True)
    def get_prihlaseni_studenti(self, studium_key, zapisny_list_key, predmet_key, termin_key):
        return []
        # TODO

    @with_key_args(True, True, True, True)
    def prihlas_na_termin(self, studium_key, zapisny_list_key, predmet_key, termin_key):
        return "Prihlasovanie v demoverzii ešte nie je implementované."

    @with_key_args(True, True, True, True)
    def odhlas_z_terminu(self, studium_key, zapisny_list_key, predmet_key, termin_key):
        return "Odhlasovanie v demoverzii ešte nie je implementované."
