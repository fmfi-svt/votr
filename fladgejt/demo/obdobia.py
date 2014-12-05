# -*- coding: utf-8 -*-

from fladgejt.structures import Obdobie
from .datumy import rok, datum, ak_rok


class DemoObdobiaMixin:
    def get_semester_obdobie(self, semester, akademicky_rok=None):
        if not akademicky_rok: akademicky_rok = ak_rok(4)
        a, b = akademicky_rok.split('/')
        if semester == "Z": return Obdobie('22.09.%s 00:00:00' % a, '19.12.%s 23:59:59' % a, '05')
        if semester == "L": return Obdobie('17.02.%s 00:00:00' % b, '23.05.%s 23:59:59' % b, '07')
        raise ValueError("Wrong semester")

    def get_skuskove_obdobie(self, semester, akademicky_rok=None):
        if not akademicky_rok: akademicky_rok = ak_rok(4)
        a, b = akademicky_rok.split('/')
        if semester == "Z": return Obdobie('15.12.%s 00:00:00' % a, '14.02.%s 23:59:59' % b, '06')
        if semester == "L": return Obdobie('12.05.%s 00:00:00' % b, '04.07.%s 23:59:59' % b, '08')
        raise ValueError("Wrong semester")
