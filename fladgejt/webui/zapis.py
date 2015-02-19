
from aisikl.app import assert_ops
from fladgejt.helpers import (
    CantOpenApplication, find_row, find_option, decode_key)
from fladgejt.structures import ZapisPredmet, ZapisVlastnost


UNAVAILABLE = "Zápis predmetov pre tento zápisný list nie je dostupný."


class WebuiZapisMixin:
    def zapis_get_zapisane_predmety(self, zapisny_list_key, cast):
        try:
            app = self._open_zapis_predmetov_app(zapisny_list_key)
        except CantOpenApplication:
            return [[], UNAVAILABLE]
        self.__zatvor_ponuku_predmetov(app)

        # Oznacime vrchol pre celu cast, aby sme videli vsetky predmety.
        app.d.castiZapisnehoListuTree.select('nR/' + cast)

        result = [ZapisPredmet(skratka=row['skratka'],
                               nazov=row['nazov'],
                               typ_vyucby=row['kodTypVyucby'],
                               semester=row['semester'],
                               kredit=row['kredit'],
                               rozsah_vyucby=row['rozsah'],
                               jazyk=row['jazyk'],
                               datum_zapisu=row['datumZapisu'],
                               aktualnost=row['aktualnost'],
                               pocet_prihlasenych=None,
                               maximalne_prihlasenych=None,
                               blok_skratka=row['skratkaBlok'],
                               blok_nazov=row['popisBlok'],
                               blok_index=None,
                               v_bloku_index=None,
                               odporucany_rocnik=None,
                               cast=row['kodCastStPlanu'])
                  for row in app.d.predmetyTable.all_rows()]
        return [result, None]

    def zapis_get_vlastnosti_programu(self, zapisny_list_key):
        try:
            app = self._open_zapis_predmetov_app(zapisny_list_key)
        except CantOpenApplication:
            return [[], UNAVAILABLE]
        self.__zatvor_ponuku_predmetov(app)

        result = [ZapisVlastnost(skratka=row['skratka'],
                                 nazov=row['nazov'],
                                 minimalny_kredit=row['kredit'],
                                 poznamka=row['poznamky'])
                  for row in app.d.vlastnostiStudProgramuTable.all_rows()]
        return [result, None]

    def zapis_plan_vyhladaj(self, zapisny_list_key, cast):
        try:
            app = self._open_zapis_predmetov_app(zapisny_list_key)
        except CantOpenApplication:
            return [[], UNAVAILABLE]
        self.__zatvor_ponuku_predmetov(app)

        # AIS ponuka styri dialogy na pridavanie predmetov:
        # (1) "Pridat predmet zo studijneho planu"
        # (2) "Pridat predmet z ponuky predmetov"
        # (3) "Pridat neabsolvovany predmet"
        # (4) "Pridat odporucany predmet"
        # Zoznam ponukanych predmetov sa da zistit cez (1), (2) aj (4). (Pre
        # (2) mozme dat vyhladat vsetky predmety a zoradit ich podla bloku. Ale
        # to je dost pomale.) My pouzivame (1), lebo v tabulke su viacere dobre
        # stlpce, ako odporucany rocnik a "oficialne poradie" predmetov. Lenze
        # tieto stlpce su schovane, takze ich najprv musime zobrazit.

        # Optimalizacia pre SC (Studijna cast): Staci otvorit iba C (Vyberove
        # predmety), mozme vypnut filtrovanie podla typu vyucby a uvidime aj
        # A a B. Ale nesmieme ich tak zapisovat, lebo AIS ich zapise ako C, co
        # na studijnom nemaju radi.

        result = []

        # Skusime kazdy vrchol stromu, co nas zaujima.
        for id, node in app.d.castiZapisnehoListuTree.nodes.items():
            if not node.is_leaf: continue
            if '/' + cast + '/' not in id: continue
            if id in ('nR/SC/A', 'nR/SC/B'): continue

            # Oznacime dany vrchol stromu.
            app.d.castiZapisnehoListuTree.select(id)

            # Stlacime "Pridat predmet zo studijneho planu".
            with app.collect_operations() as ops:
                app.d.pridatPredmetAction.execute()

            # Mozno vyskoci chyba.
            if len(ops) == 1 and ops[0].method == 'messageBox':
                return [[], ops[0].args[0]]

            # Mozno vyskoci ze ziadny zaznam.
            # TODO: Zislo by sa to ignorovanie konkretnych messageboxov.
            if len(ops) == 2:
                assert_ops(ops, 'openDialog', 'messageBox')
                if ops[1].args[0] != 'Podmienkam nevyhovuje žiadny záznam.':
                    raise AISBehaviorError("AIS displayed an error: {}".format(ops))
                ops = ops[0:1]

            # Otvori sa novy dialog.
            app.awaited_open_dialog(ops)

            # Zapneme schovane stlpce.
            want = ['kodTypVyucby', 'popis', 'poradieB', 'poradieP', 'kodCastSP']
            if any(col not in app.d.predmetyTable.column_map for col in want):
                self._show_all_columns(app, app.d.predmetyTable)

            # Zrusime filter podla odporucaneho rocniku.
            index = find_option(app.d.rocnikComboBox.options, title='')
            app.d.rocnikComboBox.select(index)

            # Ak sa da, zrusime filter podla typu vyucby.
            if app.d.typComboBox.is_really_enabled():
                index = find_option(app.d.typComboBox.options, title='')
                app.d.typComboBox.select(index)

            # Nacitame vsetky predmety.
            with app.collect_operations() as ops:
                app.d.zobrazitPredmetyButton.click()
            if ops:
                assert_ops(ops, 'messageBox')
                if ops[0].args[0] != 'Podmienkam nevyhovuje žiadny záznam.':
                    raise AISBehaviorError("AIS displayed an error: {}".format(ops))

            result.extend(ZapisPredmet(skratka=row['skratkaPredmet'],
                                       nazov=row['nazovPredmet'],
                                       typ_vyucby=row['kodTypVyucby'],
                                       semester=row['kodSemester'],
                                       kredit=row['kredit'],
                                       rozsah_vyucby=row['rozsah'],
                                       jazyk=row['jazyk'],
                                       datum_zapisu=None,
                                       aktualnost=row['kodAktualnost'],
                                       pocet_prihlasenych=row['pocetStudentov'],
                                       maximalne_prihlasenych=row['obmedzenie'],
                                       blok_skratka=row['skratkaBlok'],
                                       blok_nazov=row['popis'],
                                       blok_index=row['poradieB'],
                                       v_bloku_index=row['poradieP'],
                                       odporucany_rocnik=row['rocnik'],
                                       cast=row['kodCastSP'])
                          for row in app.d.predmetyTable.all_rows())

            # Ked sme hotovi, zavrieme dialog.
            with app.collect_operations() as ops:
                app.d.click_close_button()
            app.awaited_close_dialog(ops)

        return [result, None]

    def zapis_plan_pridaj_predmety(self, zapisny_list_key, cast,
                                   dvojice_typ_vyucby_skratka):
        try:
            app = self._open_zapis_predmetov_app(zapisny_list_key)
        except CantOpenApplication:
            return UNAVAILABLE
        self.__zatvor_ponuku_predmetov(app)

        # Zistime, ake vsetky typy vyucby chceme zapisat.
        typy_vyucby = sorted(set(
            typ_vyucby for typ_vyucby, skratka in dvojice_typ_vyucby_skratka))

        for typ_vyucby in typy_vyucby:
            # Oznacime dany vrchol stromu.
            id = 'nR/' + cast + '/' + typ_vyucby
            app.d.castiZapisnehoListuTree.select(id)

            # Stlacime "Pridat predmet zo studijneho planu".
            with app.collect_operations() as ops:
                app.d.pridatPredmetAction.execute()

            # Mozno vyskoci chyba.
            if len(ops) == 1 and ops[0].method == 'messageBox':
                return ops[0].args[0]

            # Mozno vyskoci ze ziadny zaznam.
            # TODO: Zislo by sa to ignorovanie konkretnych messageboxov.
            if len(ops) == 2:
                assert_ops(ops, 'openDialog', 'messageBox')
                if ops[1].args[0] != 'Podmienkam nevyhovuje žiadny záznam.':
                    raise AISBehaviorError("AIS displayed an error: {}".format(ops))
                ops = ops[0:1]

            # Otvori sa novy dialog.
            app.awaited_open_dialog(ops)

            # Skusime, ci uz teraz vidime vsetky hladane predmety.
            found_all = True
            for typ_vyucby_predmetu, skratka in dvojice_typ_vyucby_skratka:
                if typ_vyucby != typ_vyucby_predmetu: continue
                try:
                    find_row(
                        app.d.predmetyTable.all_rows(), skratkaPredmet=skratka)
                except KeyError:
                    found_all = False

            if not found_all:
                # Ak nevidime, zrusime filter podla odporucaneho rocniku.
                index = find_option(app.d.rocnikComboBox.options, title='')
                app.d.rocnikComboBox.select(index)

                # Nacitame vsetky predmety.
                with app.collect_operations() as ops:
                    app.d.zobrazitPredmetyButton.click()
                if ops:
                    assert_ops(ops, 'messageBox')
                    if ops[0].args[0] != 'Podmienkam nevyhovuje žiadny záznam.':
                        raise AISBehaviorError("AIS displayed an error: {}".format(ops))

            # Teraz uz by sme mali vidiet vsetky predmety, co chceme zapisat.
            # Postupne ich najdeme a zapneme checkboxy.
            for typ_vyucby_predmetu, skratka in dvojice_typ_vyucby_skratka:
                if typ_vyucby != typ_vyucby_predmetu: continue
                index = find_row(
                    app.d.predmetyTable.all_rows(), skratkaPredmet=skratka)
                app.d.predmetyTable.edit_cell('p', index, True)

            # Stlacime "OK".
            with app.collect_operations() as ops:
                app.d.enterButton.click()

            # Mozno vyskoci confirm box. (Napriklad nas upozornuje, ze niektore
            # predmety uz mame zapisane. O inych confirm boxoch nevieme, a
            # dufame, ze su neskodne.) Zvolime "Ano".
            if len(ops) == 1 and ops[0].method == 'confirmBox':
                with app.collect_operations() as ops:
                    app.confirm_box(2)

            # Mozno vyskoci chyba.
            message = None
            if len(ops) == 1 and ops[0].method == 'messageBox':
                message = ops[0].args[0]
                with app.collect_operations() as ops:
                    app.d.click_close_button()

            # Dialog sa zavrie.
            app.awaited_close_dialog(ops)

            if message: return message

        return None

    def __zatvor_ponuku_predmetov(self, app):
        if app.d.name == 'VSES260_PridaniePredmetuDlg1':
            with app.collect_operations() as ops:
                app.d.click_close_button()
            app.awaited_close_dialog(ops)

    def __otvor_ponuku_predmetov(self, app):
        if app.d.name != 'VSES260_PridaniePredmetuDlg1':
            # Oznacime vrchol SC - C. (V ponuke predmetov nezalezi, aky typ
            # vyucby zvolime, a zapise sa spravne.)
            app.d.castiZapisnehoListuTree.select('nR/SC/C')

            # Stlacime "Pridat predmet z ponuky predmetov".
            with app.collect_operations() as ops:
                app.d.pridatPredmetZPonukyAction.execute()

            # Mozno vyskoci chyba.
            if len(ops) == 1 and ops[0].method == 'messageBox':
                return ops[0].args[0]

            # Otvori sa novy dialog.
            app.awaited_open_dialog(ops)

    def __query_ponuka_predmetov(self, app, fakulta, stredisko,
                                 filter_skratka, filter_nazov):
        message = self.__otvor_ponuku_predmetov(app)
        if message:
            return message

        if (app.d.fakultaComboBox.selected_option.id == (fakulta or '') and
            app.d.predmetSkratkaTextField.value == (filter_skratka or '') and
            app.d.predmetNazovTextField.value == (filter_nazov or '') and
            app.d.strediskoSkratkaTextField.value == (stredisko or '') and
            (not stredisko or not app.d.strediskoTextTextField.value)):
            return None

        app.d.fakultaComboBox.select(find_option(app.d.fakultaComboBox.options, id=(fakulta or '')))

        app.d.predmetSkratkaTextField.write(filter_skratka or '')

        app.d.predmetNazovTextField.write(filter_nazov or '')

        if not self._select_text_ciselnik(
                app, stredisko, 'strediskoSkratkaTextField',
                app.d.zmazatStrediskoAction.component_ids[0],
                app.d.vybratStrediskoAction.component_ids[0], 'skratka'):
            return "Stredisko neexistuje."

        with app.collect_operations() as ops:
            app.d.zobrazitPredmetyAction.execute()
        if ops:
            assert_ops(ops, 'messageBox')
            if ops[0].args[0] != 'Podmienkam nevyhovuje žiadny záznam.':
                raise AISBehaviorError("AIS displayed an error: {}".format(ops))

        while not app.d.predmetyTable.is_end_of_data:
            app.d.predmetyTable.scroll_down(10)

        return None

    def zapis_ponuka_vyhladaj(self, zapisny_list_key, fakulta, stredisko,
                              filter_skratka, filter_nazov):
        try:
            app = self._open_zapis_predmetov_app(zapisny_list_key)
        except CantOpenApplication:
            return [[], UNAVAILABLE]

        # Otvorime ponuku predmetov a vyhladame predmety.
        message = self.__query_ponuka_predmetov(
            app, fakulta, stredisko, filter_skratka, filter_nazov)
        if message:
            return [[], message]

        if app.d.predmetyTable.truncated:
            message = "Neboli načítané všetky dáta. Upresnite kritériá vyhľadávania."

        result = [ZapisPredmet(skratka=row['skratkaPredmet'],
                               nazov=row['nazovPredmet'],
                               typ_vyucby=row['kodTypVyucby'],
                               semester=row['kodSemester'],
                               kredit=row['kredit'],
                               rozsah_vyucby=row['rozsah'],
                               jazyk=row['jazyk'],
                               datum_zapisu=None,
                               aktualnost=row['kodAktualnost'],
                               pocet_prihlasenych=row['pocetStudentov'],
                               maximalne_prihlasenych=row['obmedzenie'],
                               blok_skratka=row['skratkaBlok2'],
                               blok_nazov=None,
                               blok_index=None,
                               v_bloku_index=None,
                               odporucany_rocnik=None,
                               cast='SC')
                  for row in app.d.predmetyTable.loaded_rows]
        return [result, message]

    def zapis_ponuka_pridaj_predmety(self, zapisny_list_key, fakulta, stredisko,
                                     filter_skratka, filter_nazov,
                                     zvolene_skratky):
        try:
            app = self._open_zapis_predmetov_app(zapisny_list_key)
        except CantOpenApplication:
            return UNAVAILABLE

        # Otvorime ponuku predmetov a vyhladame predmety.
        message = self.__query_ponuka_predmetov(
            app, fakulta, stredisko, filter_skratka, filter_nazov)
        if message:
            return message

        # Odznacime vsetky vyznacene predmety (nemalo by sa stat).
        for row in app.d.predmetyTable.loaded_rows:
            if row['p'] == True:
                app.d.predmetyTable.edit_cell('p', row.id, False)

        # Vyznacime predmety, co si chceme zapisat.
        for skratka in zvolene_skratky:
            index = find_row(
                app.d.predmetyTable.loaded_rows, skratkaPredmet=skratka)
            app.d.predmetyTable.edit_cell('p', index, True)

        # Stlacime "OK".
        with app.collect_operations() as ops:
            app.d.enterButton.click()

        # Mozno vyskoci confirm box. (Napriklad nas upozornuje, ze niektore
        # predmety uz mame zapisane. O inych confirm boxoch nevieme, a
        # dufame, ze su neskodne.) Zvolime "Ano".
        if len(ops) == 1 and ops[0].method == 'confirmBox':
            with app.collect_operations() as ops:
                app.confirm_box(2)

        # Mozno vyskoci chyba. (Dialog zostane otvoreny.)
        if len(ops) == 1 and ops[0].method == 'messageBox':
            return ops[0].args[0]

        # Dialog sa zavrie.
        app.awaited_close_dialog(ops)

        return None

    def zapis_ponuka_options(self, zapisny_list_key):
        try:
            app = self._open_zapis_predmetov_app(zapisny_list_key)
        except CantOpenApplication:
            return [[], UNAVAILABLE]

        message = self.__otvor_ponuku_predmetov(app)
        if message:
            return [[], message]

        return [app.d.fakultaComboBox.options, None]

    def zapis_odstran_predmety(self, zapisny_list_key, cast, predmet_key_list):
        try:
            app = self._open_zapis_predmetov_app(zapisny_list_key)
        except CantOpenApplication:
            return UNAVAILABLE
        self.__zatvor_ponuku_predmetov(app)

        # Oznacime vrchol pre celu cast, aby sme videli vsetky predmety.
        app.d.castiZapisnehoListuTree.select('nR/' + cast)

        # Vyberieme v tabulke dane predmety.
        indexes = []
        for predmet_key in predmet_key_list:
            (skratka_predmetu,) = decode_key(predmet_key)
            indexes.append(find_row(
                app.d.predmetyTable.all_rows(),
                skratka=skratka_predmetu))
        app.d.predmetyTable.select(indexes)

        # Stlacime "Odobrat predmet".
        with app.collect_operations() as ops:
            app.d.odobratPredmetButton.click()

        # Mozno vyskoci confirm box. Zvolime "Ano".
        if len(ops) == 1 and ops[0].method == 'confirmBox':
            with app.collect_operations() as ops:
                app.confirm_box(2)

        # Mozno vyskoci chyba. Ak nie, sme hotovi.
        if ops:
            assert_ops(ops, 'messageBox')
            return ops[0].args[0]

        return None
