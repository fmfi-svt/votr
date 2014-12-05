# -*- coding: utf-8 -*-

from fladgejt.helpers import with_key_args
from fladgejt.structures import RegUcitelPredmetu, PrihlasenyStudent, RegPredmet
from .datumy import rok, datum, ak_rok


class DemoPredmetyMixin:
    @with_key_args(True, False)
    def get_studenti_zapisani_na_predmet(self, predmet_key, akademicky_rok):
        return [[], None]
        # TODO

    @with_key_args(True, False, False, False)
    def get_ucitelia_predmetu(self, predmet_key, akademicky_rok, semester, fakulty):
        return []
        # TODO

    def vyhladaj_predmety(
            self, akademicky_rok, fakulta, stredisko, skratka_sp,
            skratka_predmetu, nazov_predmetu, semester, stupen):
        return [[], "Vyhľadávanie predmetov ešte v demoverzii nie je implementované."]
        # TODO

    def get_register_predmetov_fakulta_options(self):
        return [dict(id=k, title=k) for k in [''] + self._fakulty]

    def get_register_predmetov_akademicky_rok_options(self):
        return [dict(id=ak_rok(y), title=ak_rok(y)) for y in range(6)]

    def get_register_predmetov_semester_options(self):
        options = ['', 'Z - Zimný semester', 'L - Letný semester']
        return [dict(id=k[0:1], title=k) for k in options]

    def get_register_predmetov_stupen_options(self):
        options = [
            "",
            "I. - bakalársky stupeň",
            "II. - úplný vysokoškolský stupeň",
            "I.II. - úplný vysokoškolský stupeň",
            "III. - doktorandský stupeň",
            "K - kontinuálne vzdelávanie",
            "N - neurčený stupeň",
        ]
        return [dict(id=k.partition(' ')[0], title=k) for k in options]
