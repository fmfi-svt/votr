import aisikl
from aisikl.app import Application


class WebuiTestAisiklMixin:

    _testing_started = set()
    _seen_types = set()

    # aby tlacidla, ktore zatvaraju dialog, boli stlacene ako posledne
    def _sort_buttons(self, buts):
        if 'enterButton' in buts:
            buts.remove('enterButton')
            buts.append('enterButton')
        if 'closeButton' in buts:
            buts.remove('closeButton')
            buts.append('closeButton')
        elif 'exitButton' in buts:
            buts.remove('exitButton')
            buts.append('exitButton')

    # ci uz otvarana aplikacia zacala byt niekedy testovana
    def _check_testing_started(self, app, ops):
        if (ops[0].method == 'openMainDialog' or ops[0].method == 'openDialog') and len(ops[0].args[0]['code']) > 0:
            if ops[0].args[0]['code'] in _testing_started:
                return True
            else:
                _testing_started.add(ops[0].args[0]['code'])
                return False

    # zaznamenavanie typov
    def _process(self, app):
        for dialog in app.dialog_stack:
            for c in dialog.components.values():
                if c.component_type not in seen_types:
                    _seen_types.add(c.component_type)
                    self.context.log('benchmark', "Saw " + str(c.component_type) + " '" + str(repr(c.id)) + "'")

    def _test_inside_app(self, app, o):
        if len(o) == 2: # kvoli AS042 -> stavy prispevku; predpokladame, ze viac ako 2 operacie tu nedostaneme
            t1 = _test_inside_app(app, o[:1])
            t2 = _test_inside_app(app, o[1:])
            if t1 == 'serverCloseApplication' or t2 == 'serverCloseApplication': # toto je len pre uplnost, asi to nenastane
                return 'serverCloseApplication'
            if t1 == 'closeDialog' or t2 == 'closeDialog':
                return 'closeDialog'
            return t1
        if o[0].method == 'openDialog':
            app.awaited_open_dialog(o)
            name = o[0].args[0]['id']
            o.pop()
            _process(app)
            buttons = [cname for cname in app.d.components if type(app.d.components[cname]) == aisikl.components.button.Button]
            _sort_buttons(buttons)
            for b in buttons:
                app.d.components[b].click()
                if len(o) > 0:
                    if _check_testing_started(app, o):
                        continue
                    t = _test_inside_app(app, o)
                    if t == 'closeDialog':
                        break
                    if t == 'serverCloseApplication':
                        return 'serverCloseApplication'
            if buttons == []: # kvoli situacii pri prihlasovani sa na skusky -> dialog podrobne info
                app.close_dialog(name)
            return 'openDialog'
        if o[0].method == 'confirmBox':
            app.confirm_box(2) # vsetko odsuhlasime
            o.pop()
            return 'confirmBox'
        if o[0].method == 'closeDialog':
            app.awaited_close_dialog(o)
            o.pop()
            return 'closeDialog'
        if o[0].method == 'abortBox':
            app.awaited_abort_box(o)
            o.pop()
            return 'abortBox'
        if o[0].method == 'startApp':
            a, ops = app.awaited_start_app(o)
            if not _check_testing_started(app, ops):
                _test_app(a, ops)
            o.pop()
            return 'startApp'
        if o[0].method == 'messageBox':
            o.pop()
            return 'messageBox'
        if o[0].method == 'refreshDialog':
            app.awaited_refresh_dialog(o)
            o.pop()
            return 'refreshDialog'
        if o[0].method == 'serverCloseApplication':
            app.close_all_dialogs()
            return 'serverCloseApplication'
        if o[0].method == 'shellExec':
            o.pop()
            return 'shellExec'

    def _test_app(self, app, ops):
        if len(ops) == 3: # kvoli aplikacii VSUB051
            app.close_all_dialogs()
            return
        if len(ops) == 2: # obcas vyskocia hned 2 okna
            app.awaited_open_main_dialog(ops[:1])
            with app.collect_operations() as o:
                o.append(ops[1])
                _test_inside_app(app, o)
        else:
            app.awaited_open_main_dialog(ops)
        _process(app)
        buttons = [cname for cname in app.d.components if type(app.d.components[cname]) == aisikl.components.button.Button]
        _sort_buttons(buttons)
        for b in buttons:
            with app.collect_operations() as ops:
                try: # tento blok je tu kvoli refreshom v aplikacii VSES333
                    app.d.components[b].click()
                except KeyError:
                    continue
                if len(ops) > 0:
                    if ops[0].method == 'serverCloseApplication':
                        app.close_all_dialogs()
                        break
                    if _check_testing_started(app, ops):
                        continue
                    if _test_inside_app(app, ops) == 'serverCloseApplication':
                        break

    def test(self):
        apps = aisikl.portal.get_apps(self.context)
        del apps['SSSP031'] # pri otvarani vyhodi AISParseError
        for a in apps:
            app, ops = Application.open(self.context, apps[a].url)
            if not _check_testing_started(app, ops):
                _test_app(app, ops)
        self.context.log('benchmark', 'Test successfully finished')
