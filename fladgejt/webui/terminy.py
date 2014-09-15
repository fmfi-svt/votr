
from aisikl.exceptions import AISBehaviorError
from fladgejt.helpers import find_row, find_option, with_key_args
from fladgejt.structures import Predmet, Termin, PrihlasenyStudent


class WebuiTerminyMixin:
    def __vyber_oba_semestre(self, app):
        index = find_option(app.d.semesterComboBox.options, title='')
        if app.d.semesterComboBox.selected_index != index:
            app.d.semesterComboBox.select(index)
            app.d.filterAction.execute()

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
        result = [Termin(...) #TODO
                  for row in app.d.terminyTable.all_rows()]
        return result

    @with_key_args(True, True)
    def get_vypisane_terminy(self, studium_key, zapisny_list_key):
        app = self._open_terminy_hodnotenia_app(studium_key, zapisny_list_key)

        self.__vyber_oba_semestre(app)

        result = []

        for row in app.d.predmetyTable.all_rows():
            if row['pocetAktualnychTerminov'] == '0': continue
            result.extend(self.get_vypisane_terminy_predmetu(
                studium_key, zapisny_list_key, row['skratka']))

        return result

    def __open_vyber_terminu_dialog(self, app, predmet_key):
        # Nie je memoized. Caller musi dialog zavriet, aby memoizovana
        # aplikacia bola zase v konzistentnom stave.

        self.__vyber_oba_semestre(app)

        # Vyberieme spravny riadok v tabulke predmetov.
        (skratka,) = predmet_key
        index = find_row(app.d.predmetyTable.all_rows(), skratka=skratka)
        app.d.predmetyTable.select(index)

        # Stlacime button "Prihlasit sa na termin" dole.
        with app.collect_operations() as ops:
            app.d.pridatButton.click()

        # Otvori sa novy dialog.
        app.awaited_open_dialog(ops)

    @with_key_args(True, True, True)
    def get_vypisane_terminy_predmetu(self, studium_key, zapisny_list_key, predmet_key):
        app = self._open_terminy_hodnotenia_app(studium_key, zapisny_list_key)
        self.__open_vyber_terminu_dialog(app, predmet_key)

        result = [Termin(...) #TODO
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
        self.__open_vyber_terminu_dialog(app, predmet_key)

        # Vyberieme spravny riadok. Ak v tabulke nie je, vypneme "Zobrazit len
        # aktualne terminy", stlacime nacitavaci button a skusime znovu.
        datum, cas, miestnost, poznamka = termin_key
        try:
            index = find_row(
                app.d.zoznamTerminovTable.all_rows(),
                dat=datum, cas=cas, miestnosti=miestnost, poznamka=poznamka)
        except KeyError:
            index = None
        if index is None:
            app.d.aktualneTerminyCheckBox.set_to(False)
            app.d.zobrazitTerminyAction.click()
            index = find_row(
                app.d.zoznamTerminovTable.all_rows(),
                dat=datum, cas=cas, miestnosti=miestnost, poznamka=poznamka)
        app.d.zoznamTerminovTable.select(index)

        # Stlacime "Zobrazit zoznam prihlasenych".
        with app.collect_operations() as ops:
            app.d.zobrazitZoznamPrihlasenychAction.execute()

        # Otvori sa zoznam prihlasenych.
        app.awaited_open_dialog(ops)

        # Vytiahneme data z tabulky.
        result = [PrihlasenyStudent(...) #TODO
                  for row in app.d.prihlaseniTable.all_rows()]

        # Stlacime zatvaraci button na zozname prihlasenych.
        with app.collect_operations() as ops:
            app.d.click_close_button()

        # Dialog sa zavrie.
        app.awaited_close_dialog(ops)

        # Stlacime zatvaraci button na zozname terminov.
        with app.collect_operations() as ops:
            app.d.click_close_button()

        # Dialog sa zavrie.
        app.awaited_close_dialog(ops)

        return result

    @with_key_args(True, True, True, True)
    def prihlas_na_termin(self, studium_key, zapisny_list_key, predmet_key, termin_key):
        app = self._open_terminy_hodnotenia_app(studium_key, zapisny_list_key)
        self.__open_vyber_terminu_dialog(app, predmet_key)

        # Vyberieme spravny riadok.
        datum, cas, miestnost, poznamka = termin_key
        app.d.zoznamTerminovTable.select(find_row(
            app.d.zoznamTerminovTable.all_rows(),
            dat=datum, cas=cas, miestnosti=miestnost, poznamka=poznamka))

        # Stlacime OK.
        with app.collect_operations() as ops:
            app.d.enterButton.click()

        # Dialog sa zavrie.
        # TODO: skontrolovat.
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
        app.d.zoznamTerminovTable.select(find_row(
            app.d.zoznamTerminovTable.all_rows(),
            dat=datum, cas=cas, miestnosti=miestnost, poznamka=poznamka))

        # Stlacime "Odhlasit sa z terminu".
        with app.collect_operations() as ops:
            app.d.odstranitButton.click()

        # Vyskoci confirm box, ci sa naozaj chceme odhlasit. Stlacime "Ano".
        assert_ops(ops, 'confirmBox')
        with app.collect_operations() as ops:
            app.confirm_box(2)

        # Vyskoci message box, ze sa podarilo.
        assert_ops(ops, 'messageBox')
        if ops[0].args[0] != '\u010cinnos\u0165 \xfaspe\u0161ne dokon\u010den\xe1.':
            raise AISBehaviorError("AIS displayed an error: {}".format(ops))
