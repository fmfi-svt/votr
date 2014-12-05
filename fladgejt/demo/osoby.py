# -*- coding: utf-8 -*-

from fladgejt.structures import RegOsoba
from .datumy import rok, datum, ak_rok


class DemoOsobyMixin:
    def __init__(self):
        super().__init__()
        self._fakulty = [
            'Červená fakulta',
            'Zelená fakulta',
            'Fakulta modrých vied',
        ]

    def vyhladaj_osobu(
            self, meno, priezvisko, absolvent, student, zamestnanec,
            akademicky_rok, fakulta, studijny_program, uchadzaci, prvy_rocnik,
            druhy_rocnik, treti_rocnik, stvrty_rocnik, piaty_rocnik,
            siesty_rocnik, siedmy_rocnik, osmy_rocnik, absolventi):
        return [[], "Vyhľadávanie osôb ešte v demoverzii nie je implementované."]
        # TODO

    def get_register_osob_akademicky_rok_options(self):
        return [dict(id=ak_rok(y), title=ak_rok(y)) for y in range(6)]

    def get_register_osob_fakulty(self):
        return [dict(id=k, title=k) for k in [''] + self._fakulty]
