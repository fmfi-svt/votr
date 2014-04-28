# Docasny testovaci skript.
# Spusti ho priamo, alebo sprav "from test1 import ctx".

import os, sys
cookie = os.getenv('AIS_COOKIE')
if not cookie: sys.exit('musis dat export AIS_COOKIE="hodnota cosign-filteru"')
origin = os.getenv('AIS_ORIGIN', 'ais2.uniba.sk')

from aisikl.context import Context
ctx = Context('https://'+origin+'/', { 'cosign-filter-'+origin: cookie })

n = ctx.request_html('/ais/login.do').find(class_='user-name')
if not (n and n.get_text()): raise Exception('login neuspesny, asi zly cookie')

if __name__ == '__main__':
    import aisikl.portal
    print(aisikl.portal.get_modules(ctx))
