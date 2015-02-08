
from aisikl.app import assert_ops
from fladgejt.helpers import (
    CantOpenApplication, find_row, find_option, encode_key, decode_key)
from fladgejt.structures import Predmet, Termin, PrihlasenyStudent


class WebuiTerminyMixin:
    def __vyber_oba_semestre(self, app):
        index = find_option(app.d.semesterComboBox.options, title='')
        if app.d.semesterComboBox.selected_index != index:
            app.d.semesterComboBox.select(index)
            with app.collect_operations() as ops:
                app.d.filterAction.execute()
            if ops:
                assert_ops(ops, 'messageBox')

    def get_vidim_terminy_hodnotenia(self, zapisny_list_key):
        try:
            self._open_terminy_hodnotenia_app(zapisny_list_key)
        except CantOpenApplication:
            return False
        return True

    def get_predmety(self, zapisny_list_key):
        app = self._open_terminy_hodnotenia_app(zapisny_list_key)

        self.__vyber_oba_semestre(app)

        result = [Predmet(skratka=row['skratka'],
                          nazov=row['nazov'],
                          typ_vyucby=row['kodTypVyucby'],
                          semester=row['semester'],
                          kredit=row['kredit'])
                  for row in app.d.predmetyTable.all_rows()]
        return result

    def get_prihlasene_terminy(self, zapisny_list_key):
        app = self._open_terminy_hodnotenia_app(zapisny_list_key)

        # V dolnom combo boxe dame "Zobrazit terminy: Vsetkych predmetov".
        app.d.zobrazitTerminyComboBox.select(0)

        # Stlacime button vedla combo boxu.
        app.d.zobrazitTerminyAction.execute()

        studium_key, akademicky_rok = decode_key(zapisny_list_key)

        # Vytiahneme tabulku terminov.
        result = [Termin(datum=row['dat'],
                         cas=row['cas'],
                         miestnost=row['miestnosti'],
                         pocet_prihlasenych=row['pocetPrihlasenych'],
                         maximalne_prihlasenych=row['maxPocet'],
                         hodnotiaci=row['hodnotiaci'],
                         prihlasovanie=row['prihlasovanie'],
                         odhlasovanie=row['odhlasovanie'],
                         poznamka=row['poznamka'],
                         skratka_predmetu=row['predmetSkratka'],
                         nazov_predmetu=row['predmetNazov'],
                         hodnotenie_terminu=row['znamka'],
                         hodnotenie_predmetu=row['hodnPredmetu'],
                         moznost_prihlasit=row['moznostPrihlasenia'],
                         datum_prihlasenia=row['datumPrihlas'],
                         datum_odhlasenia=row['datumOdhlas'],
                         akademicky_rok=akademicky_rok,
                         zapisny_list_key=zapisny_list_key)
                  for row in app.d.terminyTable.all_rows()
                  if not row['datumOdhlas']]
        return result

    def get_vypisane_terminy(self, zapisny_list_key):
        app = self._open_terminy_hodnotenia_app(zapisny_list_key)

        self.__vyber_oba_semestre(app)

        result = []

        for row in app.d.predmetyTable.all_rows():
            if row['pocetAktualnychTerminov'] == '0': continue
            result.extend(self.get_vypisane_terminy_predmetu(
                zapisny_list_key, encode_key((row['skratka'],))))

        return result

    def __open_vyber_terminu_dialog(self, app):
        # Caller musi dialog potom zavriet, aby otvorena aplikacia bola zase
        # v konzistentnom stave pre dalsieho co ju pouzije.

        # Stlacime button "Prihlasit sa na termin" dole.
        with app.collect_operations() as ops:
            app.d.pridatButton.click()

        # Otvori sa novy dialog.
        app.awaited_open_dialog(ops)

    def __select_predmet_row(self, app, predmet_key):
        self.__vyber_oba_semestre(app)

        (skratka,) = decode_key(predmet_key)
        index = find_row(app.d.predmetyTable.all_rows(), skratka=skratka)
        app.d.predmetyTable.select(index)

        return app.d.predmetyTable.all_rows()[index]

    def get_vypisane_terminy_predmetu(self, zapisny_list_key, predmet_key):
        app = self._open_terminy_hodnotenia_app(zapisny_list_key)

        predmet_row = self.__select_predmet_row(app, predmet_key)
        self.__open_vyber_terminu_dialog(app)

        studium_key, akademicky_rok = decode_key(zapisny_list_key)

        result = [Termin(datum=row['dat'],
                         cas=row['cas'],
                         miestnost=row['miestnosti'],
                         pocet_prihlasenych=row['pocetPrihlasenych'],
                         maximalne_prihlasenych=row['maxPocet'],
                         hodnotiaci=row['hodnotiaci'],
                         prihlasovanie=row['prihlasovanie'],
                         odhlasovanie=row['odhlasovanie'],
                         poznamka=row['poznamka'],
                         skratka_predmetu=predmet_row['skratka'],
                         nazov_predmetu=predmet_row['nazov'],
                         hodnotenie_terminu="",
                         hodnotenie_predmetu="",
                         moznost_prihlasit=row['moznostPrihlasenia'],
                         datum_prihlasenia="",
                         datum_odhlasenia="",
                         akademicky_rok=akademicky_rok,
                         zapisny_list_key=zapisny_list_key)
                  for row in app.d.zoznamTerminovTable.all_rows()]

        # Stlacime zatvaraci button.
        with app.collect_operations() as ops:
            app.d.click_close_button()

        # Dialog sa zavrie.
        app.awaited_close_dialog(ops)

        return result

    def get_prihlaseni_studenti(self, termin_key):
        zapisny_list_key, predmet_key, datum, cas, miestnost, poznamka = (
            decode_key(termin_key))

        app = self._open_terminy_hodnotenia_app(zapisny_list_key)

        self.__vyber_oba_semestre(app)
        self.__select_predmet_row(app, predmet_key)

        app.d.zobrazitTerminyAction.execute()
        try:
            index = find_row(
                app.d.terminyTable.all_rows(),
                dat=datum, cas=cas, miestnosti=miestnost, poznamka=poznamka)
        except KeyError:
            index = None

        # Ak sa pozerame na stary zapisny list, vyber_terminov_dialog
        # bude disabled, preto termin musi byt v hlavnom dialogu.
        if index is not None:
            app.d.terminyTable.select(index)
            # Stlacime "Zobrazit zoznam prihlasenych".
            with app.collect_operations() as ops:
                app.d.zoznamPrihlasenychStudentovAction.execute()

            return self.__process_prihlaseni_studenti_list(app, ops)
        else:
            # zapisny_list_key a predmet_key uz sme selectli predtym.
            return self.__get_prihlaseni_studenti_cez_vyber_terminu(app,
                datum, cas, miestnost, poznamka)

    def __get_prihlaseni_studenti_cez_vyber_terminu(self, app, datum, cas,
                                                    miestnost, poznamka):
        self.__open_vyber_terminu_dialog(app)

        # Vyberieme spravny riadok. Ak v tabulke nie je, vypneme "Zobrazit len
        # aktualne terminy", stlacime nacitavaci button a skusime znovu.
        try:
            index = find_row(
                app.d.zoznamTerminovTable.all_rows(),
                dat=datum, cas=cas, miestnosti=miestnost, poznamka=poznamka)
        except KeyError:
            index = None
        if index is None:
            app.d.aktualneTerminyCheckBox.set_to(False)
            app.d.zobrazitTerminyAction.execute()
            index = find_row(
                app.d.zoznamTerminovTable.all_rows(),
                dat=datum, cas=cas, miestnosti=miestnost, poznamka=poznamka)
        app.d.zoznamTerminovTable.select(index)

        # Stlacime "Zobrazit zoznam prihlasenych".
        with app.collect_operations() as ops:
            app.d.zobrazitZoznamPrihlasenychAction.execute()

        result = self.__process_prihlaseni_studenti_list(app, ops)

        # Stlacime zatvaraci button na zozname terminov.
        with app.collect_operations() as ops:
            app.d.click_close_button()

        # Dialog sa zavrie.
        app.awaited_close_dialog(ops)

        return result

    def __process_prihlaseni_studenti_list(self, app, ops):
        # Otvori sa zoznam prihlasenych.
        app.awaited_open_dialog(ops)

        # Vytiahneme data z tabulky.
        result = [PrihlasenyStudent(sp_skratka=row['skratka'],
                                    datum_prihlasenia=row['datumPrihlas'],
                                    plne_meno=row['plneMeno'],
                                    rocnik=row['rocnik'],
                                    email=row['email'])
                  for row in app.d.prihlaseniTable.all_rows()]

        # Stlacime zatvaraci button na zozname prihlasenych.
        with app.collect_operations() as ops:
            app.d.click_close_button()

        # Dialog sa zavrie.
        app.awaited_close_dialog(ops)

        return result

    def prihlas_na_termin(self, termin_key):
        zapisny_list_key, predmet_key, datum, cas, miestnost, poznamka = (
            decode_key(termin_key))

        app = self._open_terminy_hodnotenia_app(zapisny_list_key)
        self.__select_predmet_row(app, predmet_key)
        self.__open_vyber_terminu_dialog(app)

        # Vyberieme spravny riadok.
        app.d.zoznamTerminovTable.select(find_row(
            app.d.zoznamTerminovTable.all_rows(),
            dat=datum, cas=cas, miestnosti=miestnost, poznamka=poznamka))

        # Stlacime OK.
        with app.collect_operations() as ops:
            app.d.enterButton.click()

        message = None
        if ops and ops[0].method == 'messageBox':
            assert_ops(ops, 'messageBox')
            message = ops[0].args[0]
            with app.collect_operations() as ops:
                app.d.click_close_button()

        # Dialog sa zavrie.
        app.awaited_close_dialog(ops)

        return message

    def odhlas_z_terminu(self, termin_key):
        zapisny_list_key, predmet_key, datum, cas, miestnost, poznamka = (
            decode_key(termin_key))
        (skratka_predmetu,) = decode_key(predmet_key)

        app = self._open_terminy_hodnotenia_app(zapisny_list_key)

        # V dolnom combo boxe dame "Zobrazit terminy: Vsetkych predmetov".
        app.d.zobrazitTerminyComboBox.select(0)

        # Stlacime button vedla combo boxu.
        app.d.zobrazitTerminyAction.execute()

        # Vyberieme spravny riadok.
        app.d.terminyTable.select(find_row(
            app.d.terminyTable.all_rows(),
            dat=datum, cas=cas, miestnosti=miestnost, poznamka=poznamka,
            predmetSkratka=skratka_predmetu))

        # Stlacime "Odhlasit sa z terminu".
        with app.collect_operations() as ops:
            app.d.odstranitButton.click()

        # Vyskoci confirm box, ci sa naozaj chceme odhlasit. Stlacime "Ano".
        assert_ops(ops, 'confirmBox')
        with app.collect_operations() as ops:
            app.confirm_box(2)

        if ops:
            assert_ops(ops, 'messageBox')
            if ops[0].args[0] != 'Činnosť úspešne dokončená.':
                return ops[0].args[0]

        return None
