# Docasny testovaci skript.
# Spusti ho priamo, alebo sprav "from test1 import ctx".

import os, sys
import json
cookie = os.getenv('AIS_COOKIE')
if not cookie: sys.exit('musis dat export AIS_COOKIE="hodnota cosign-filteru"')
origin = os.getenv('AIS_ORIGIN', 'int-dev.uniba.sk')

name, _, cookie = cookie.rpartition('=')
if name and name != 'cosign-filter-'+origin:
    raise Exception('cookie by sa mal volat cosign-filter-'+origin)

from aisikl.context import Context
ctx = Context('https://'+origin+':8443/', { 'cosign-filter-'+origin: cookie })

n = ctx.request_json('/')
try:
    json_object = json.loads(n)
except ValueError:
    raise Exception('login neuspesny, asi zly cookie')
else:
    if not json_object['response']['authenticated']:
        raise Exception('login neuspesny, asi zly cookie')

if __name__ == '__main__':
    
   

    from fladgejt.rest import RestClient

    rest = RestClient(ctx)

    studia = rest.get_studia()

    print(rest.get_zapisne_listy(studia[0]))

    print(rest.get_prehlad_kreditov(studia[0]))
