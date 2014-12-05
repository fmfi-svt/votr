# -*- coding: utf-8 -*-

from fladgejt.helpers import with_key_args
from fladgejt.structures import Studium, ZapisnyList, Hodnotenie
from .datumy import rok, datum, ak_rok


class DemoStudiumMixin:
    def __init__(self):
        super().__init__()
        self._studia = [
            Studium('DEM', 'demológia', '(Jednoodborové štúdium, bakalársky I. st., denná forma)', datum(6,9,0), datum(28,6,3), '6', '1234', '99'),
            Studium('mDEM', 'demológia', '(Jednoodborové štúdium, magisterský II. st., denná forma)', datum(9,9,3), '', '4', '1235', '2'),
        ]
        self._zapisne_listy = {
            self._studia[0].key: [
                ZapisnyList(ak_rok(0), '1', 'DEM', 'demológia', datum(6,9,0)),
                ZapisnyList(ak_rok(1), '2', 'DEM', 'demológia', datum(7,9,1)),
                ZapisnyList(ak_rok(2), '3', 'DEM', 'demológia', datum(8,9,2)),
            ],
            self._studia[1].key: [
                ZapisnyList(ak_rok(3), '1', 'mDEM', 'demológia', datum(9,9,3)),
                ZapisnyList(ak_rok(4), '2', 'mDEM', 'demológia', datum(10,9,4)),
            ],
        }

    def get_som_student(self):
        return True

    def get_studia(self):
        return self._studia

    @with_key_args(True)
    def get_zapisne_listy(self, studium_key):
        return self._zapisne_listy[studium_key]

    @with_key_args(True)
    def get_prehlad_kreditov(self, studium_key):
        result = []
        message = None
        for zapisny_list in self.get_zapisne_listy(studium_key):
            hodnotenia, message = self.get_hodnotenia(studium_key, zapisny_list.key)
            result.extend(hodnotenia)
        return [result, message]
