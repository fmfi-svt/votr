
from aisikl.app import Application, assert_ops
from fladgejt.webui.pool import pooled_app
from fladgejt.helpers import find_option, find_row, with_key_args
from fladgejt.structures import RegUcitelPredmetu, PrihlasenyStudent, RegPredmet


class WebuiPredmetyMixin:
    @pooled_app
    def _open_register_predmetov(self):
        url = '/ais/servlets/WebUIServlet?appClassName=ais.gui.vs.st.VSST060App&kodAplikacie=VSST060&uiLang=SK'
        app, ops = Application.open(self.context, url)
        app.awaited_open_main_dialog(ops)
        return app

    def get_informacny_list(self, kod_predmetu, akademicky_rok=None):
        app = self._open_register_predmetov()

        # Vyberieme akademicky rok.
        if akademicky_rok is None:
            index = 0
        else:
            index = find_option(
                app.d.akRokComboBox.options, title=akademicky_rok)
        app.d.akRokComboBox.select(index)

        # Napiseme kod predmetu.
        app.d.skratkaPredmetuTextField.write(kod_predmetu)

        # Stlacime nacitavaci button (sipku dole).
        app.d.zobrazitPredmetyButton.click()

        if not app.d.zoznamPredmetovTable.loaded_rows:
            return None
        # TODO: zdokumentovat, ze ak matchuju viacere informacne listy, je
        # undefined behavior ktory vratime. (asi vzdy ten prvy, ale kto vie ako
        # ich AIS zoradi.)

        # Stlacime v menu "Informacny list".
        with app.collect_operations() as ops:
            app.d.infListMenuItem.click()

        # Otvori sa dialog na vyber formatu.
        app.awaited_open_dialog(ops)

        # Vyberieme vrchny riadok. TODO: fakt chceme ten?
        app.d.sablonyTable.select(0)

        # Stlacime OK.
        with app.collect_operations() as ops:
            app.d.enterButton.click()

        # Dialog sa zavrie a otvori sa "prosim cakajte", tak cakame.
        assert_ops(ops, 'closeDialog', 'abortBox')
        app.close_dialog(*ops[0].args)
        with app.collect_operations() as ops:
            app.abort_box()

        # Otvori sa vysledne PDF.
        url = app.awaited_shell_exec(ops)
        return app.context.request_text(url)

    def __query_dialog(self, app, akademicky_rok, fakulta=None, semester=None,
                       stupen_predmetu=None, typ_predmetu=None,
                       zobrazit_len=None, skratka_predmetu=None,
                       nazov_predmetu=None, cislo_predmetu=None,
                       stredisko=None, skratka_sp=None):
        message = []

        app.d.fakultaUniverzitaComboBox.select(find_option(app.d.fakultaUniverzitaComboBox.options, id=(fakulta or '')))

        app.d.semesterComboBox.select(find_option(app.d.semesterComboBox.options, id=(semester or '')))

        app.d.stupenPredmetuComboBox.select(find_option(app.d.stupenPredmetuComboBox.options, id=(stupen_predmetu or '')))

        app.d.typPredmetuComboBox.select(find_option(app.d.typPredmetuComboBox.options, id=(typ_predmetu or '')))

        app.d.zobrazitLenComboBox.select(find_option(app.d.zobrazitLenComboBox.options, id=(zobrazit_len or '')))

        app.d.skratkaPredmetuTextField.write(skratka_predmetu or '')

        app.d.nazovPredmetuTextField.write(nazov_predmetu or '')

        app.d.cisloPredmetuNumberControl.write(cislo_predmetu or '')

        if not self._select_ciselnik(app, stredisko, 'strediskoTextField', 'zmazatStrediskoButton', 'vybratStrediskoAction', 'skratka'):
            message.append("Stredisko neexistuje.")

        if not self._select_ciselnik(app, skratka_sp, 'skratkaStudProgramuTextField', 'zmazatStudProgramButton', 'vybratStudProgramAction', 'skratka'):
            message.append("Študijný program neexistuje.")

        if app.d.vyucujuciTextField.value:
            app.d.odobratVyucujucehoButton.click()

        app.d.akRokComboBox.select(
            find_option(app.d.akRokComboBox.options, id=akademicky_rok))

        return message

    @with_key_args(True, False)
    def get_studenti_zapisani_na_predmet(self, predmet_key, akademicky_rok):
        (skratka_predmetu,) = predmet_key
        app = self._open_register_predmetov()

        self.__query_dialog(app, akademicky_rok, skratka_predmetu=skratka_predmetu.split('/')[1])

        app.d.zobrazitPredmetyButton.click()

        predmet_index = find_row(app.d.zoznamPredmetovTable.all_rows(), skratka=skratka_predmetu)
        app.d.zoznamPredmetovTable.select(predmet_index)

        predmet_row = app.d.zoznamPredmetovTable.all_rows()[predmet_index]
        predmet = RegPredmet(skratka=predmet_row['skratka'],
                             nazov=predmet_row['nazov'],
                             semester=predmet_row['kodSemester'],
                             stredisko=predmet_row['stredisko'],
                             fakulta=predmet_row['FakUniv'],
                             rozsah_vyucby=predmet_row['rozsah'],
                             konanie=predmet_row['konanie'],
                             cudzi_nazov=predmet_row['nazovJ'],
                             kredit=predmet_row['kredit'])
        with app.collect_operations() as ops:
            app.d.poctyPrihlasenychStudentovAction.execute()

        app.awaited_open_dialog(ops)

        app.d.dataTable.select(
            find_row(app.d.dataTable.all_rows(), skratka=skratka_predmetu))

        with app.collect_operations() as ops:
            app.d.zoznamStudentovAction.execute()

        app.awaited_open_dialog(ops)

        studenti = [PrihlasenyStudent(sp_skratka=row['studProgSkratka'],
                                      datum_prihlasenia=row['datumZapisania'],
                                      plne_meno=row['plneMeno'],
                                      rocnik=row['rokRocnik'],
                                      email=row['email'])
                    for row in app.d.zaradeniStudentiTable.all_rows()]

        # zatvarame dialog so zoznamom studentov
        with app.collect_operations() as ops:
            app.d.closeButton.click()

        app.awaited_close_dialog(ops)

        # zatvarame dialog pocty studentov
        with app.collect_operations() as ops:
            app.d.closeButton.click()

        app.awaited_close_dialog(ops)

        return [studenti, predmet]

    def _open_nastenka_predmetu(self):
        url = '/ais/servlets/WebUIServlet?appClassName=ais.gui.vs.st.VSST157App&kodAplikacie=VSST157&uiLang=SK'
        app, ops = Application.open(self.context, url)
        app.awaited_open_main_dialog(ops)
        return app

    @with_key_args(True, False, False, False)
    def get_ucitelia_predmetu(self, predmet_key, fakulta, akademicky_rok, semester):
        (skratka_predmetu,) = predmet_key

        app = self._open_nastenka_predmetu()

        fakulta_index = find_option(app.d.fakultaComboBox.options, id=fakulta)
        if app.d.fakultaComboBox.selected_index != fakulta_index:
            app.d.fakultaComboBox.select(fakulta_index)
            app.d.potvrditOrgJednotkuButton.click()

        semester_index = find_option(app.d.semesterComboBox.options, id=semester)
        if app.d.semesterComboBox.selected_index != semester_index:
            app.d.semesterComboBox.select(semester_index)

        # automaticky nacitavanie ucitelov do tabulky
        app.d.nacitavatAutomatickyCheckBox.set_to(True)

        akademicky_rok_index = find_option(app.d.rokComboBox.options, title=akademicky_rok)
        if app.d.rokComboBox.selected_index != akademicky_rok_index:
            app.d.rokComboBox.select(akademicky_rok_index)

        app.d.skratkaTextField.write(skratka_predmetu)

        # nastavime zobrazenie vsetkych predmetov, nie len tych co
        # mame zapisane.
        zobrazit_index = find_option(app.d.zobrazitComboBox.options, id="VSETKY")
        if app.d.zobrazitComboBox.selected_index != zobrazit_index:
            app.d.zobrazitComboBox.select(zobrazit_index)

        app.d.nacitatPredmetyButton.click()

        app.d.skupinaPredmetovTable.select(
            find_row(app.d.skupinaPredmetovTable.all_rows(), skratka=skratka_predmetu))

        ucitelia = [RegUcitelPredmetu(plne_meno=row['plneMeno'],
                                      typ=row['typVyucujuceho'])
                    for row in app.d.vyucujuciTable.all_rows()]
        return ucitelia
