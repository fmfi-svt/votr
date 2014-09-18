# -*- coding: utf-8 -*-

from aisikl.app import Application, assert_ops
from fladgejt.helpers import memoized, find_option, find_row
from fladgejt.structures import Predmet

class WebuiPredmetyMixin:
    @memoized
    def _open_register_predmetov(self):
        url = '/ais/servlets/WebUIServlet?appClassName=ais.gui.vs.st.VSST060App&kodAplikacie=VSST060&uiLang=SK'
        app, ops = Application.open(self.context, url)
        app.awaited_open_main_dialog(ops)
        return app

    def __prepare_dialog(self):
        app = self._open_register_predmetov()

        if app.d.fakultaUniverzitaComboBox.selected_index != 0:
            app.d.fakultaUniverzitaComboBox.select(0)

        if app.d.semesterComboBox.selected_index != 0:
            app.d.semesterComboBox.select(0)

        if app.d.stupenPredmetuComboBox.selected_index != 0:
            app.d.stupenPredmetuComboBox.select(0)

        if app.d.typPredmetuComboBox.selected_index != 0:
            app.d.typPredmetuComboBox.select(0)

        if app.d.zobrazitLenComboBox.selected_index != 0:
            app.d.zobrazitLenComboBox.select(0)

        if app.d.skratkaPredmetuTextField.value != '':
            app.d.skratkaPredmetuTextField.write('')

        if app.d.nazovPredmetuTextField.value != '':
            app.d.nazovPredmetuTextField.write('')

        if app.d.cisloPredmetuNumberControl.bdvalue != '':
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

    def vyhladaj_predmety(self, fakulta=None, stredisko=None, skratka_sp=None, skratka_predmetu=None, nazov_predmetu=None, akademicky_rok=None, semester=None, stupen=None):
        app = self._open_register_predmetov()
        self.__prepare_dialog()

        message = None
        predmety = []

        if fakulta is not None:
            index = find_option(app.d.fakultaUniverzitaComboBox.options, id=fakulta)
            app.d.fakultaUniverzitaComboBox.select(index)
            
        if semester is not None:
            index = find_option(app.d.semesterComboBox.options, id=semester)
            app.d.semesterComboBox.select(index)
            

        if akademicky_rok is None:
            index = 0
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
                    return [predmety, "Stredisko neexistuje."]

                app.d.table.select(index)

                # Stlacime zatvaraci button.
                with app.collect_operations() as ops:
                    app.d.enterButton.click()

                # Dialog sa zavrie.
                app.awaited_close_dialog(ops)

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
                    return [predmety, "Štúdijný program neexistuje."]

                app.d.table.select(index)

                # Stlacime zatvaraci button.
                with app.collect_operations() as ops:
                    app.d.enterButton.click()

                # Dialog sa zavrie.
                app.awaited_close_dialog(ops)


        if skratka_predmetu is not None:
            app.d.skratkaPredmetuTextField.write(skratka_predmetu)

        if nazov_predmetu is not None:
            app.d.nazovPredmetuTextField.write(nazov_predmetu)

        if stupen is not None:
            index = find_option(app.d.stupenPredmetuComboBox.options, id=stupen)
            app.d.stupenPredmetuComboBox.select(index)

        # Uz mame nastavene vsetky parametre vyhladavania, stlacime nacitavaci button.
        with app.collect_operations() as ops:
            app.d.zobrazitPredmetyButton.click()

        if len(ops) == 1:
            assert_ops(ops, 'messageBox')
            message = ops[0].args[0]            

        while not app.d.zoznamPredmetovTable.is_end_of_data:
            app.d.zoznamPredmetovTable.scroll_down(10)
        if app.d.zoznamPredmetovTable.truncated:
            message = "Neboli načítané všetky dáta. Upresnite prosím kritéria vyhľadávania."

        if app.d.zoznamPredmetovTable.loaded_rows:
            predmety = [Predmet(skratka=row['skratka'],
                              nazov=row['nazov'],
                              typ_vyucby=row['kodTypPredmetu'],
                              semester=row['kodSemester'],
                              kredit=row['kredit'])
                      for row in app.d.zoznamPredmetovTable.loaded_rows]

        return [predmety, message]

    def get_fakulta_options(self):
        app = self._open_register_predmetov()
        self.__prepare_dialog()

        return app.d.fakultaUniverzitaComboBox.options

    def get_akademicky_rok_options(self):
        app = self._open_register_predmetov()
        self.__prepare_dialog()

        return app.d.akRokComboBox.options

    def get_semester_options(self):
        app = self._open_register_predmetov()
        self.__prepare_dialog()

        return app.d.semesterComboBox.options

    def get_stupen_options(self):
        app = self._open_register_predmetov()
        self.__prepare_dialog()

        return app.d.stupenPredmetuComboBox.options

    def get_stredisko_options(self, fakulta=None):
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

    def get_studijny_program_options(self, fakulta=None):
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
