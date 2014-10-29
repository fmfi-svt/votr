
from aisikl.exceptions import AISBehaviorError
from aisikl.app import assert_ops
from fladgejt.helpers import find_row, find_option, with_key_args
from fladgejt.structures import Predmet, Termin, PrihlasenyStudent


class WebuiTerminyMixin:
    def __vyber_oba_semestre(self, app):
        index = find_option(app.d.semesterComboBox.options, title='')
        if app.d.semesterComboBox.selected_index != index:
            app.d.semesterComboBox.select(index)
            app.d.filterAction.execute()

    @with_key_args(True, True)
    def get_vidim_terminy_hodnotenia(self, studium_key, zapisny_list_key):
        try:
            self._open_terminy_hodnotenia_app(studium_key, zapisny_list_key)
        except AISBehaviorError as e:
            if (getattr(e, 'operations', None) == [] and
                getattr(e, 'expected_methods', None) == ['startApp']):
                return False
            raise
        return True

    @with_key_args(True, True)
    def get_predmety(self, studium_key, zapisny_list_key):
        app = self._open_terminy_hodnotenia_app(studium_key, zapisny_list_key)

        self.__vyber_oba_semestre(app)

        result = [Predmet(skratka=row['skratka'],
                          nazov=row['nazov'],
                          typ_vyucby=row['kodTypVyucby'],
                          semester=row['semester'],
                          kredit=row['kredit'])
                  for row in app.d.predmetyTable.all_rows()]
        return result

    @with_key_args(True, True)
    def get_prihlasene_terminy(self, studium_key, zapisny_list_key):
        app = self._open_terminy_hodnotenia_app(studium_key, zapisny_list_key)

        # V dolnom combo boxe dame "Zobrazit terminy: Vsetkych predmetov".
        app.d.zobrazitTerminyComboBox.select(0)

        # Stlacime button vedla combo boxu.
        app.d.zobrazitTerminyAction.execute()

        # Vytiahneme tabulku terminov.
        (akademicky_rok,) = zapisny_list_key
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
                         akademicky_rok=akademicky_rok)
                  for row in app.d.terminyTable.all_rows()
                  if not row['datumOdhlas']]
        return result

    @with_key_args(True, True)
    def get_vypisane_terminy(self, studium_key, zapisny_list_key):
        app = self._open_terminy_hodnotenia_app(studium_key, zapisny_list_key)

        self.__vyber_oba_semestre(app)

        result = []

        for row in app.d.predmetyTable.all_rows():
            if row['pocetAktualnychTerminov'] == '0': continue
            result.extend(self.get_vypisane_terminy_predmetu(
                studium_key, zapisny_list_key, (row['skratka'],)))

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

        (skratka,) = predmet_key
        index = find_row(app.d.predmetyTable.all_rows(), skratka=skratka)
        app.d.predmetyTable.select(index)

        return app.d.predmetyTable.all_rows()[index]

    @with_key_args(True, True, True)
    def get_vypisane_terminy_predmetu(self, studium_key, zapisny_list_key, predmet_key):
        app = self._open_terminy_hodnotenia_app(studium_key, zapisny_list_key)

        predmet_row = self.__select_predmet_row(app, predmet_key)
        self.__open_vyber_terminu_dialog(app)

        (akademicky_rok,) = zapisny_list_key
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
                         moznost_prihlasit=row['moznostPrihlasenia'],
                         akademicky_rok=akademicky_rok)
                  for row in app.d.zoznamTerminovTable.all_rows()]

        # Stlacime zatvaraci button.
        with app.collect_operations() as ops:
            app.d.click_close_button()

        # Dialog sa zavrie.
        app.awaited_close_dialog(ops)

        return result

    @with_key_args(True, True, True, True)
    def get_prihlaseni_studenti(self, studium_key, zapisny_list_key, predmet_key, termin_key):
        app = self._open_terminy_hodnotenia_app(studium_key, zapisny_list_key)

        self.__vyber_oba_semestre(app)
        self.__select_predmet_row(app, predmet_key)

        datum, cas, miestnost, poznamka = termin_key

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
            return self.__get_prihlaseni_studenti_cez_vyber_terminu(app, termin_key)

    def __get_prihlaseni_studenti_cez_vyber_terminu(self, app, termin_key):
        self.__open_vyber_terminu_dialog(app)

        datum, cas, miestnost, poznamka = termin_key

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

    @with_key_args(True, True, True, True)
    def prihlas_na_termin(self, studium_key, zapisny_list_key, predmet_key, termin_key):
        app = self._open_terminy_hodnotenia_app(studium_key, zapisny_list_key)
        predmet_row = self.__select_predmet_row(app, predmet_key)
        self.__open_vyber_terminu_dialog(app)

        # Vyberieme spravny riadok.
        datum, cas, miestnost, poznamka = termin_key
        app.d.zoznamTerminovTable.select(find_row(
            app.d.zoznamTerminovTable.all_rows(),
            dat=datum, cas=cas, miestnosti=miestnost, poznamka=poznamka))

        # Stlacime OK.
        with app.collect_operations() as ops:
            app.d.enterButton.click()

        # Dialog sa zavrie.
        app.awaited_close_dialog(ops)

    @with_key_args(True, True, True, True)
    def odhlas_z_terminu(self, studium_key, zapisny_list_key, predmet_key, termin_key):
        app = self._open_terminy_hodnotenia_app(studium_key, zapisny_list_key)

        # V dolnom combo boxe dame "Zobrazit terminy: Vsetkych predmetov".
        app.d.zobrazitTerminyComboBox.select(0)

        # Stlacime button vedla combo boxu.
        app.d.zobrazitTerminyAction.execute()

        # Vyberieme spravny riadok.
        datum, cas, miestnost, poznamka = termin_key
        app.d.terminyTable.select(find_row(
            app.d.terminyTable.all_rows(),
            dat=datum, cas=cas, miestnosti=miestnost, poznamka=poznamka))

        # Stlacime "Odhlasit sa z terminu".
        with app.collect_operations() as ops:
            app.d.odstranitButton.click()

        # Vyskoci confirm box, ci sa naozaj chceme odhlasit. Stlacime "Ano".
        assert_ops(ops, 'confirmBox')
        app.confirm_box(2)
