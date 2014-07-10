# Docasny testovaci skript.
# Spusti ho priamo, alebo sprav "from test1 import ctx".

import os
import sys
import json
cookie = os.getenv('AIS_COOKIE')
if not cookie:
    sys.exit('musis dat export AIS_COOKIE="hodnota cosign-filteru"')
origin = os.getenv('AIS_ORIGIN', 'int-dev.uniba.sk')

name, _, cookie = cookie.rpartition('=')
if name and name != 'cosign-filter-' + origin:
    raise Exception('cookie by sa mal volat cosign-filter-' + origin)

from aisikl.context import Context
ctx = Context('https://' + origin + ':8443/',
              {'cosign-filter-' + origin: cookie})

try:
    initial = ctx.request_json('/')
except ValueError:
    raise Exception('login neuspesny, asi zly cookie')
else:
    if not initial['authenticated']:
        raise Exception('login neuspesny, asi zly cookie')

if __name__ == '__main__':

    from fladgejt.rest import RestClient

    rest = RestClient(ctx)

    studia = rest.get_studia()

    zapisne_listy = rest.get_zapisne_listy(
        studia[0].sp_skratka,
        studia[0].zaciatok)
    print(zapisne_listy)

    terminy = rest.get_vypisane_terminy(
        studia[0].sp_skratka,
        studia[0].zaciatok,
        zapisne_listy[2].akademicky_rok)
    print(terminy)

    print()

    print(
        rest.get_prihlaseny_studenti(
            studia[0].sp_skratka,
            studia[0].zaciatok,
            zapisne_listy[2].akademicky_rok,
            "FMFI.KAI/1-AIN-636/00",
            "2014-01-22",
            "09:00",
            "FMFI I 007,FMFI I 009",
            "RNDr. Martin Homola, PhD."))
