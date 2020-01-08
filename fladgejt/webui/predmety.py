# -*- coding: utf-8 -*-
import base64

from aisikl.app import Application, assert_ops
from fladgejt.webui.pool import pooled_app
from fladgejt.helpers import find_option, find_row, decode_key
from fladgejt.structures import RegUcitelPredmetu, PrihlasenyStudent, RegPredmet


class WebuiPredmetyMixin:
    @pooled_app
    def _open_register_predmetov(self):
        url = '/ais/servlets/WebUIServlet?fajr=A&appClassName=ais.gui.vs.st.VSST060App&kodAplikacie=VSST060&uiLang=SK'
        app, ops = Application.open(self.context, url)
        app.awaited_open_main_dialog(ops)
        return app

    def get_informacny_list(self, kod_predmetu, akademicky_rok):
        app = self._open_register_predmetov()

        stredisko, _, zvysok = decode_key(kod_predmetu)[0].partition('/')
        skratka = zvysok.rpartition('/')[0]

        # Napiseme stredisko a skratku predmetu.
        self.__query_dialog(app, akademicky_rok, stredisko=stredisko,
            skratka_predmetu=skratka)

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
        with app.collect_operations() as ops2:
            app.abort_box(*ops[1].args)

        # Vratime zakodove PDF.
        url = app.awaited_shell_exec(ops2)
        return base64.b64encode(url.content).decode()

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

        if not self._select_text_ciselnik(
                app, stredisko, 'skratkaStrediskaTextField',
                'zmazatStrediskoButton', 'vybratStrediskoButton', 'skratka'):
            message.append("Stredisko neexistuje.")

        if not self._select_text_ciselnik(
                app, skratka_sp, 'skratkaStudProgramuTextField',
                'zmazatStudProgramButton', 'vybratStudProogramButton',
                'skratka'):
            message.append("Študijný program neexistuje.")

        if app.d.vyucujuciTextField.value:
            app.d.odobratVyucujucehoButton.click()

        app.d.akRokComboBox.select(
            find_option(app.d.akRokComboBox.options, id=akademicky_rok))

        return ' '.join(message) or None

    def get_studenti_zapisani_na_predmet(self, predmet_key, akademicky_rok):
        (skratka_predmetu,) = decode_key(predmet_key)
        app = self._open_register_predmetov()

        # Ak AIS prihlasenie vyprsalo, AIS nam stale dovoli otvorit register
        # predmetov, ale nie dialog poctu prihlasenych studentov. Ak to tak
        # vyzera, skontrolujeme ci netreba nove prihlasenie.
        if not app.d.poctyPrihlasenychStudentovMenuItem.enabled:
            self.check_connection()

        self.__query_dialog(app, akademicky_rok, skratka_predmetu='/'.join(skratka_predmetu.split('/')[1:-1]))

        app.d.zobrazitPredmetyButton.click()

        if not app.d.zoznamPredmetovTable.all_rows():
            # predmet nebol najdeny (napriklad uz je prilis stary ale napriek
            # tomu ho mam v mojom hodnoteni)
            return [[], None]

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

        try:
            app.d.dataTable.select(
                find_row(app.d.dataTable.all_rows(), skratka=skratka_predmetu))
        except KeyError:
            with app.collect_operations() as ops:
                app.d.closeButton.click()

            app.awaited_close_dialog(ops)

            return [[], predmet]

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

    @pooled_app
    def _open_nastenka_predmetu(self):
        url = '/ais/servlets/WebUIServlet?fajr=A&appClassName=ais.gui.vs.st.VSST157App&kodAplikacie=VSST157&uiLang=SK'
        app, ops = Application.open(self.context, url)
        app.awaited_open_main_dialog(ops)
        return app

    def get_ucitelia_predmetu(self, predmet_key, akademicky_rok, semester, fakulty):
        (skratka_predmetu,) = decode_key(predmet_key)

        app = self._open_nastenka_predmetu()

        fakulta = fakulty.split(',')[0]
        fakulta_index = find_option(app.d.fakultaComboBox.options, id=fakulta)
        if app.d.fakultaComboBox.selected_index != fakulta_index:
            app.d.fakultaComboBox.select(fakulta_index)
            app.d.potvrditOrgJednotkuButton.click()

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

        mozne_semestre = [semester] if semester else ["Z", "L"]
        for semester in mozne_semestre:
            semester_index = find_option(app.d.semesterComboBox.options, id=semester)
            if app.d.semesterComboBox.selected_index != semester_index:
                app.d.semesterComboBox.select(semester_index)

            app.d.nacitatPredmetyButton.click()

            if app.d.skupinaPredmetovTable.all_rows():
                app.d.skupinaPredmetovTable.select(
                    find_row(app.d.skupinaPredmetovTable.all_rows(), skratka=skratka_predmetu))

                ucitelia = [RegUcitelPredmetu(plne_meno=row['plneMeno'],
                                              typ=row['typVyucujuceho'])
                            for row in app.d.vyucujuciTable.all_rows()]
                return ucitelia

        return []

    def vyhladaj_predmety(self, akademicky_rok, fakulta, stredisko, skratka_sp,
                          skratka_predmetu, nazov_predmetu, semester, stupen):
        app = self._open_register_predmetov()

        message = None
        predmety = []

        message = self.__query_dialog(app,
                                      akademicky_rok,
                                      fakulta=fakulta,
                                      semester=semester,
                                      stupen_predmetu=stupen,
                                      skratka_predmetu=skratka_predmetu,
                                      nazov_predmetu=nazov_predmetu,
                                      stredisko=stredisko,
                                      skratka_sp=skratka_sp)

        if message:
            return [predmety, message]

        app.d.zobrazitPredmetyButton.click()

        while not app.d.zoznamPredmetovTable.is_end_of_data:
            app.d.zoznamPredmetovTable.scroll_down(10)
        if app.d.zoznamPredmetovTable.truncated:
            message = "Neboli načítané všetky dáta. Upresnite kritériá vyhľadávania."

        predmety = [RegPredmet(skratka=row['skratka'],
                               nazov=row['nazov'],
                               semester=row['kodSemester'],
                               stredisko=row['stredisko'],
                               fakulta=row['FakUniv'],
                               rozsah_vyucby=row['rozsah'],
                               konanie=row['konanie'],
                               cudzi_nazov=row['nazovJ'],
                               kredit=row['kredit'])
                    for row in app.d.zoznamPredmetovTable.loaded_rows]

        return [predmety, message]

    def get_register_predmetov_fakulta_options(self):
        app = self._open_register_predmetov()

        return app.d.fakultaUniverzitaComboBox.options

    def get_register_predmetov_akademicky_rok_options(self):
        app = self._open_register_predmetov()

        return app.d.akRokComboBox.options

    def get_register_predmetov_semester_options(self):
        app = self._open_register_predmetov()

        return app.d.semesterComboBox.options

    def get_register_predmetov_stupen_options(self):
        app = self._open_register_predmetov()

        return app.d.stupenPredmetuComboBox.options
