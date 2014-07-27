import datetime
from fladgejt.structures import Prihlasena_osoba


def get_aktualny_datetime():
    """ Aktualny datetime """
    return datetime.datetime(datetime.today().year, 12, 22, 16)


def get_aktualna_prihlasena_osoba():
    return Prihlasena_osoba(skratka='mINF',
                            datum_prihlasenia=datetime(
                                datetime.today().year, 1, 7, 19, 1),
                            plne_meno='Bc. Ján von Informačný',
                            rocnik=1)
