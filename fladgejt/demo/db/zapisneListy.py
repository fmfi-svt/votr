from fladgejt.structures import ZapisnyList
from datetime import datetime


def get_zapisneListy(studium_id):
    if studium_id == 1:
        return [ZapisnyList(id=1,
                            akademicky_rok='{}/{}'.format(
                                datetime.today().year - 4, datetime.today().year - 3),
                            rocnik=1,
                            sp_skratka='INF',
                            sp_popis='informatika',
                            datum_zapisu=datetime(datetime.today().year - 4, 9, 1)),
                ZapisnyList(id=2,
                            akademicky_rok='{}/{}'.format(
                                datetime.today().year - 3, datetime.today().year - 2),
                            rocnik=2,
                            sp_skratka='INF',
                            sp_popis='informatika',
                            datum_zapisu=datetime(datetime.today().year - 3, 9, 1)),
                ZapisnyList(id=3,
                            akademicky_rok='{}/{}'.format(
                                datetime.today().year - 2, datetime.today().year - 1),
                            rocnik=3,
                            sp_skratka='INF',
                            sp_popis='informatika',
                            datum_zapisu=datetime(datetime.today().year - 2, 9, 1))]
    elif studium_id == 2:
        return [ZapisnyList(id=4,
                            akademicky_rok='{}/{}'.format(
                                datetime.today().year - 1, datetime.today().year),
                            rocnik=1,
                            sp_skratka='INF',
                            sp_popis='informatika',
                            datum_zapisu=datetime(datetime.today().year, 9, 1))]
    else:
        raise KeyError('Požadované studium_id neexistuje.')
