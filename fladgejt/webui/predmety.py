
from aisikl.app import Application, assert_ops
from fladgejt.helpers import memoized, find_row
from fladgejt.structures import Predmet

class WebuiPredmetyMixin:
    @memoized
    def _open_register_predmetov(self):
        url = '/ais/servlets/WebUIServlet?appClassName=ais.gui.vs.st.VSST060App&kodAplikacie=VSST060&uiLang=SK'
        app = Application(self.context)
        ops = app.init(url)

        dlg = app.open_main_dialog(*ops[0].args)
        return dlg

    def get_informacny_list(self, kod_predmetu, akademicky_rok=None):
        app = self._open_register_predmetov()
        dlg = app.main_dialog

        # Vyberieme akademicky rok.
        if akademicky_rok is None:
            index = 0
        else:
            index = find_row(dlg.akRokComboBox.options, title=akademicky_rok)
        dlg.akRokComboBox.select(index)

        # Napiseme kod predmetu.
        dlg.skratkaPredmetuTextField.write(kod_predmetu)

        # Stlacime nacitavaci button (sipku dole).
        dlg.zobrazitPredmetyButton.click()

        if not dlg.zoznamPredmetovTable.loaded_rows:
            return None
        # TODO: zdokumentovat, ze ak matchuju viacere informacne listy, je
        # undefined behavior ktory vratime. (asi vzdy ten prvy, ale kto vie ako
        # ich AIS zoradi.)

        # Stlacime v menu "Informacny list".
        with app.collect_operations() as ops:
            dlg.infListMenuItem.click()

        # Otvori sa dialog na vyber formatu.
        dlg2 = app.awaited_open_dialog(ops)

        # Vyberieme vrchny riadok. TODO: fakt chceme ten?
        dlg2.sablonyTable.select(0)

        # Stlacime OK.
        with app.collect_operations() as ops:
            dlg2.enterButton.click()

        # Dialog sa zavrie a otvori sa "prosim cakajte", tak cakame.
        assert_ops(ops, 'closeDialog', 'abortBox')
        app.close_dialog(*ops[0].args)
        with app.collect_operations() as ops:
            app.abort_box()

        # Otvori sa vysledne PDF.
        url = app.awaited_shell_exec(ops)
        return app.context.request_text(url)

    def vyhladaj_predmety(self, fakulta = None, stredisko = None, skratka_sp = None, skratka_predmetu = None, nazov_predmetu = None, akademicky_rok = None, semester = None, stupen = None):
        dlg = self._open_register_predmetov()

        if fakulta is None:
            index = 0
        else:
            index = find_row(dlg.fakultaUniverzitaComboBox.options, title=fakulta)
        dlg.fakultaUniverzitaComboBox.select(index)

        if semester is None:
            index = 0
        else:
            index = find_row(dlg.semesterComboBox.options, title=semester)
        dlg.semesterComboBox.select(index)

        if akademicky_rok is None:
            index = 0
        else:
            index = find_row(dlg.akRokComboBox.options, title=akademicky_rok)
        dlg.akRokComboBox.select(index)

        if stredisko is not None:
            dlg.strediskoTextField.write(stredisko)
            dlg.vybratStrediskoAction.execute()
            # TODO: osetrit ak sa zada nevhodny text, v tom pripade sa otvori dialog...

        if skratka_sp is not None:
            dlg.skratkaStudProgramuTextField.write(skratka_sp)
            dlg.vybratStudProgramAction.execute()
            # TODO: osetrit ak sa zada nevhodny text, v tom pripade sa otvori dialog...

        if skratka_predmetu is not None:
            dlg.skratkaPredmetuTextField.write(skratka_predmetu)

        if nazov_predmetu is not None:
            dlg.nazovPredmetuTextField.write(nazov_predmetu)

        if stupen is None:
            index = 0
        else:
            index = find_row(dlg.stupenPredmetuComboBox.options, title=stupen)
        dlg.stupenPredmetuComboBox.select(index)

        dlg.zobrazitPredmetyButton.click()

        if not dlg.zoznamPredmetovTable.loaded_rows:
            return None

        result = [Predmet(skratka=row['skratka'],
                          nazov=row['nazov'],
                          typ_vyucby=row['kodTypPredmetu'],
                          semester=row['kodSemester'],
                          kredit=row['kredit'])
                  for row in dlg.zoznamPredmetovTable.all_rows()]
        
        return result
