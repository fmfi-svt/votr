# -*- coding: utf-8 -*-

from aisikl.exceptions import AISBehaviorError
from aisikl.app import Application, assert_ops
from fladgejt.webui.pool import pooled_app
from fladgejt.helpers import find_option, find_row, get_aktualny_akademicky_rok
from fladgejt.structures import PredmetRegistra


class WebuiPredmetyMixin:
    @pooled_app
    def _open_register_predmetov(self):
        url = '/ais/servlets/WebUIServlet?appClassName=ais.gui.vs.st.VSST060App&kodAplikacie=VSST060&uiLang=SK'
        app, ops = Application.open(self.context, url)
        app.awaited_open_main_dialog(ops)
        return app

    def __prepare_dialog(self):
        app = self._open_register_predmetov()

        app.d.fakultaUniverzitaComboBox.select(0)

        app.d.semesterComboBox.select(0)

        app.d.stupenPredmetuComboBox.select(0)

        app.d.typPredmetuComboBox.select(0)

        app.d.zobrazitLenComboBox.select(0)

        app.d.skratkaPredmetuTextField.write('')

        app.d.nazovPredmetuTextField.write('')

        app.d.cisloPredmetuNumberControl.write('')

        if app.d.strediskoTextField.is_editable():
            app.d.strediskoTextField.write('')
        else:
            app.d.zmazatStrediskoButton.click()

        if app.d.skratkaStudProgramuTextField.is_editable():
            app.d.skratkaStudProgramuTextField.write('')
        else:
            app.d.zmazatStudProgramButton.click()

        if app.d.odobratVyucujucehoButton.is_really_enabled():
            app.d.odobratVyucujucehoButton.click()

        app.d.akRokComboBox.select(
            find_option(app.d.akRokComboBox.options, id=get_aktualny_akademicky_rok()))

    def get_informacny_list(self, kod_predmetu, akademicky_rok=None):
        app = self._open_register_predmetov()

        # Vyberieme akademicky rok.
        if akademicky_rok is None:
            index = get_aktualny_akademicky_rok()
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

    def vyhladaj_predmety(self, fakulta=None, stredisko=None, skratka_sp=None, skratka_predmetu=None, nazov_predmetu=None, akademicky_rok=None, semester=None, stupen=None):
        app = self._open_register_predmetov()
        self.__prepare_dialog()

        message = None
        predmety = []

        if fakulta is not None:
            app.d.fakultaUniverzitaComboBox.select(find_option(app.d.fakultaUniverzitaComboBox.options, id=fakulta))

        if semester is not None:
            app.d.semesterComboBox.select(find_option(app.d.semesterComboBox.options, id=semester))

        if akademicky_rok is None:
            index = find_option(app.d.akRokComboBox.options, id=get_aktualny_akademicky_rok())
        else:
            index = find_option(app.d.akRokComboBox.options, id=akademicky_rok)
        app.d.akRokComboBox.select(index)

        if stredisko is not None:
            # Napiseme skratku strediska do textfieldu, ak je jednoznacna
            # AIS ju automaticky vyberie.
            app.d.strediskoTextField.write(stredisko)

            # Na zaklade napisanej skratky skusime vybrat stredisko.
            # Ak je viacero skratiek s rovnakym prefixom, alebo taka
            # skratka neexistuje otvori sa dialog so strediskami.
            with app.collect_operations() as ops:
                app.d.vybratStrediskoAction.execute()

            # Ak bola skratka nejednoznacna
            if len(ops) == 1:
                assert_ops(ops, 'openDialog')

                if ops[0].args[1] != 'Zabezpečujúce strediská':
                    raise AISBehaviorError("AIS opened an unexpected dialog: {}".format(ops))

                app.awaited_open_dialog(ops)

                # Skusime najst skratku medzi strediskami v tabulke
                try:
                    index = find_row(app.d.table.all_rows(), skratka=stredisko)
                except KeyError:
                    message = "Stredisko neexistuje."

                app.d.table.select(index)

                # Stlacime zatvaraci button.
                with app.collect_operations() as ops:
                    app.d.enterButton.click()

                # Dialog sa zavrie.
                app.awaited_close_dialog(ops)

                if message:
                    return [predmety, message]

        if skratka_sp is not None:
            # Napiseme skratku studijneho programu do textfieldu,
            # ak je jednoznacna AIS ju automaticky vyberie.
            app.d.skratkaStudProgramuTextField.write(skratka_sp)

            # Na zaklade napisanej skratky skusime vybrat studijny program.
            # Ak je viacero skratiek s rovnakym prefixom, alebo taka
            # skratka neexistuje otvori sa dialog so studijnymi programami.
            with app.collect_operations() as ops:
                app.d.vybratStudProgramAction.execute()

            if len(ops) == 1:
                assert_ops(ops, 'openDialog')

                if ops[0].args[1] != 'Študijné programy':
                    raise AISBehaviorError("AIS opened an unexpected dialog: {}".format(ops))

                app.awaited_open_dialog(ops)
                # Skusime najst skratku medzi studijnymi programami v tabulke
                try:
                    index = find_row(app.d.table.all_rows(), skratka=skratka_sp)
                except KeyError:
                    message = "Štúdijný program neexistuje."

                app.d.table.select(index)

                # Stlacime zatvaraci button.
                with app.collect_operations() as ops:
                    app.d.enterButton.click()

                # Dialog sa zavrie.
                app.awaited_close_dialog(ops)

                if message:
                    return [predmety, message]

        if skratka_predmetu is not None:
            app.d.skratkaPredmetuTextField.write(skratka_predmetu)

        if nazov_predmetu is not None:
            app.d.nazovPredmetuTextField.write(nazov_predmetu)

        if stupen is not None:
            app.d.stupenPredmetuComboBox.select(find_option(app.d.stupenPredmetuComboBox.options, id=stupen))

        # Uz mame nastavene vsetky parametre vyhladavania, stlacime nacitavaci button.
        with app.collect_operations() as ops:
            app.d.zobrazitPredmetyButton.click()

        if len(ops) == 1:
            assert_ops(ops, 'messageBox')
            message = ops[0].args[0]

        while not app.d.zoznamPredmetovTable.is_end_of_data:
            app.d.zoznamPredmetovTable.scroll_down(10)
        if app.d.zoznamPredmetovTable.truncated:
            message = "Neboli načítané všetky dáta. Upresnite kritériá vyhľadávania."

        predmety = [PredmetRegistra(skratka=row['skratka'],
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
        self.__prepare_dialog()

        return app.d.fakultaUniverzitaComboBox.options

    def get_register_predmetov_akademicky_rok_options(self):
        app = self._open_register_predmetov()
        self.__prepare_dialog()

        return [app.d.akRokComboBox.options, app.d.akRokComboBox.selected_option]

    def get_register_predmetov_semester_options(self):
        app = self._open_register_predmetov()
        self.__prepare_dialog()

        return app.d.semesterComboBox.options

    def get_register_predmetov_stupen_options(self):
        app = self._open_register_predmetov()
        self.__prepare_dialog()

        return app.d.stupenPredmetuComboBox.options

    def get_register_predmetov_stredisko_options(self, fakulta=None):
        app = self._open_register_predmetov()
        self.__prepare_dialog()

        if fakulta is None:
            index = 0
        else:
            index = find_option(app.d.fakultaUniverzitaComboBox.options, id=fakulta)
        app.d.fakultaUniverzitaComboBox.select(index)

        # Otvorime dialog so strediskami
        with app.collect_operations() as ops:
            app.d.vybratStrediskoAction.execute()

        assert_ops(ops, 'openDialog')

        if ops[0].args[1] != 'Zabezpečujúce strediská':
            raise AISBehaviorError("AIS opened an unexpected dialog: {}".format(ops))

        app.awaited_open_dialog(ops)

        message = None
        while not app.d.table.is_end_of_data:
            app.d.table.scroll_down(10)
        if app.d.table.truncated:
            message = "Neboli načítané všetky dáta. Upresnite prosím kritéria vyhľadávania."
        result = [app.d.table.loaded_rows, message]

        # Stlacime zatvaraci button pre strediskovy dialog.
        with app.collect_operations() as ops:
            app.d.enterButton.click()

        # Dialog sa zavrie.
        app.awaited_close_dialog(ops)

        return result

    def get_register_predmetov_studijny_program_options(self, fakulta=None):
        app = self._open_register_predmetov()
        self.__prepare_dialog()

        if fakulta is None:
            index = 0
        else:
            index = find_option(app.d.fakultaUniverzitaComboBox.options, id=fakulta)
        app.d.fakultaUniverzitaComboBox.select(index)

        # Otvorime dialog so studijnymi programami
        with app.collect_operations() as ops:
            app.d.vybratStudProgramAction.execute()

        assert_ops(ops, 'openDialog')

        if ops[0].args[1] != 'Študijné programy':
            raise AISBehaviorError("AIS opened an unexpected dialog: {}".format(ops))

        app.awaited_open_dialog(ops)

        message = None
        while not app.d.table.is_end_of_data:
            app.d.table.scroll_down(10)
        if app.d.table.truncated:
            message = "Neboli načítané všetky dáta. Upresnite prosím kritéria vyhľadávania."
        result = [app.d.table.loaded_rows, message]

        # Stlacime zatvaraci button pre strediskovy dialog.
        with app.collect_operations() as ops:
            app.d.enterButton.click()

        # Dialog sa zavrie.
        app.awaited_close_dialog(ops)

        return result
