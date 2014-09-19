# Docasny testovaci skript.
# Spusti ho priamo, alebo sprav "from test1 import ctx".

import os, sys
cookie = os.getenv('AIS_COOKIE')
if not cookie: sys.exit('musis dat export AIS_COOKIE="hodnota cosign-filteru"')
origin = os.getenv('AIS_ORIGIN', 'ais2.uniba.sk')

name, _, cookie = cookie.rpartition('=')
if name and name != 'cosign-filter-'+origin:
    raise Exception('cookie by sa mal volat cosign-filter-'+origin)

from aisikl.context import Context
ctx = Context({ 'cosign-filter-'+origin: cookie }, ais_url='https://'+origin+'/')

n = ctx.request_html('/ais/login.do').find(class_='user-name')
if not (n and n.get_text()): raise Exception('login neuspesny, asi zly cookie')

if __name__ == '__main__':
    import aisikl.portal
    apps = aisikl.portal.get_apps(ctx)
    print(apps)

    from aisikl.app import Application, assert_ops
    app, ops = Application.open(ctx, apps['VSES017'].url)
    dlg = app.awaited_open_main_dialog(ops)

    #dlg.detailStudentaButton.click()
    #dlg.nacitatButton.click()

    with app.collect_operations() as ops:
        dlg.terminyHodnoteniaAction.execute()
    app2, ops = app.awaited_start_app(ops)
    dlg2 = app2.awaited_open_main_dialog(ops)
    print(dlg2.components.keys())
