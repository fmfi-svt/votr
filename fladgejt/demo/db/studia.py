from datetime import datetime
from fladgejt.structures import Studium


def get_studia():
    return [Studium(id=1,
                    sp_skratka='INF',
                    sp_popis='informatika',
                    sp_doplnujuce_udaje='(Jednoodborové štúdium, bakalársky I. st., denná forma)',
                    zaciatok=datetime(datetime.today().year - 4, 9, 2),
                    koniec=datetime(datetime.today().year-1, 6, 27),
                    sp_dlzka=6,
                    sp_cislo=17821,
                    rok_studia=3),
            Studium(id=2,
                    sp_skratka='mINF',
                    sp_popis='informatika',
                    sp_doplnujuce_udaje='(Jednoodborové štúdium, magisterský II. st., denná forma)',
                    zaciatok=datetime(datetime.today().year-1, 9, 2),
                    koniec=None,
                    sp_dlzka=4,
                    sp_cislo=17822,
                    rok_studia=1)]
