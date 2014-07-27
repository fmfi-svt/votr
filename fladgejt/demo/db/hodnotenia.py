from datetime import datetime
from fladgejt.structures import Hodnotenie, Priemer


def get_hodnotenia():
    return [Hodnotenie(id=1,
                       akademicky_rok='{}/{}'.format(
                           datetime.today().year, datetime.today().year + 1),
                       skratka='FMFI.KI/2-INF-113/00',
                       nazov='Kombinatorická matalýza (2)',
                       typ_vyucby='B',
                       semester='Z',
                       kredit=6,
                       hodn_znamka='B',
                       hodn_termin='R - Riadny termín',
                       hodn_datum=datetime(datetime.today().year, 1, 25).date(),
                       hodn_znamka_popis='veľmi dobre'),
            Hodnotenie(id=2,
                       akademicky_rok='{}/{}'.format(
                           datetime.today().year, datetime.today().year + 1),
                       skratka='FMFI.KI/1-INF-170/00',
                       nazov='Operačné systémy',
                       typ_vyucby='A',
                       semester='L',
                       kredit=5,
                       hodn_znamka='A',
                       hodn_termin='R - Riadny termín',
                       hodn_datum=datetime(datetime.today().year, 1, 22).date(),
                       hodn_znamka_popis='výborný')]


def get_priemery():
    return [Priemer(id=1,
                    akademicky_rok='{}/{}'.format(
                        datetime.today().year - 4, datetime.today().year - 3),
                    nazov='AkadR',
                    semester=None,
                    ziskany_kredit=18,
                    predmetov=6,
                    neabsolvovanych=0,
                    studijny_priemer=1.31,
                    vazeny_priemer=1.31,
                    pokusy_priemer=1.62,
                    datum_vypoctu=datetime(datetime.today().year - 3, 9, 1).date()),
            Priemer(id=2,
                    akademicky_rok='{}/{}'.format(
                        datetime.today().year - 3, datetime.today().year - 2),
                    nazov='AkadR',
                    semester=None,
                    ziskany_kredit=20,
                    predmetov=4,
                    neabsolvovanych=0,
                    studijny_priemer=1.45,
                    vazeny_priemer=1.51,
                    pokusy_priemer=1.71,
                    datum_vypoctu=datetime(datetime.today().year - 2, 9, 1).date()),
            Priemer(id=3,
                    akademicky_rok='{}/{}'.format(
                        datetime.today().year - 2, datetime.today().year - 1),
                    nazov='AkadR',
                    semester=None,
                    ziskany_kredit=11,
                    predmetov=3,
                    neabsolvovanych=0,
                    studijny_priemer=1.21,
                    vazeny_priemer=1.33,
                    pokusy_priemer=1.47,
                    datum_vypoctu=datetime(datetime.today().year - 1, 9, 1).date()),
            Priemer(id=4,
                    akademicky_rok='{}/{}'.format(
                        datetime.today().year - 1, datetime.today().year),
                    nazov='Sem',
                    semester='Z',
                    ziskany_kredit=22,
                    predmetov=5,
                    neabsolvovanych=0,
                    studijny_priemer=1.18,
                    vazeny_priemer=1.29,
                    pokusy_priemer=1.35,
                    datum_vypoctu=datetime.today().date())]
