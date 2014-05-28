
from aisikl.app import Application, assert_ops
from fladgejt.helpers import memoized, find_row

class WebuiPredmetyMixin:
    @memoized
    def _open_register_predmetov(self):
        url = '/ais/servlets/WebUIServlet?appClassName=ais.gui.vs.st.VSST060App&kodAplikacie=VSST060&uiLang=SK'
        app, ops = Application.open(self.context, url)
        app.awaited_open_main_dialog(ops)
        return app

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
