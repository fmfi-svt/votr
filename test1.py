# Docasny testovaci skript.

import os, sys
cookie = os.getenv('AIS_COOKIE')
if not cookie: sys.exit('musis dat export AIS_COOKIE="hodnota cosign-filteru"')
origin = os.getenv('AIS_ORIGIN', 'ais2.uniba.sk')

import requests
conn = requests.Session()
conn.base_url = 'https://' + origin
conn.cookies.set('cosign-filter-' + origin, cookie)

r = conn.get(conn.base_url + '/ais/login.do')
r.raise_for_status()
if '<div class="user-name"></div>' in r.text or '<div class="user-name">' not in r.text:
    raise Exception('nepodarilo sa prihlasit, asi zly cookie')

if __name__ == '__main__':
    import aisikl.portal
    print(aisikl.portal.get_modules(conn))
