# -*- coding: utf-8 -*-

from fladgejt.helpers import with_key_args
from fladgejt.structures import Hodnotenie, Priemer
from .datumy import rok, datum, ak_rok


class DemoHodnoteniaMixin:
    @with_key_args(True, True)
    def get_hodnotenia(self, studium_key, zapisny_list_key):
        return [[], "Predmety a hodnotenia v demoverzii ešte nie sú implementované."]
        # TODO

    @with_key_args(True, True)
    def get_priemery(self, studium_key, zapisny_list_key):
        return [[], "Priemery v demoverzii ešte nie sú implementované."]
        # TODO
