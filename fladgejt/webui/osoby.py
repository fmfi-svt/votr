# -*- coding: utf-8 -*-

from aisikl.app import Application, assert_ops
from fladgejt.webui.pool import pooled_app
from fladgejt.helpers import find_option
from fladgejt.structures import RegOsoba


class WebuiOsobyMixin:
    @pooled_app
    def _open_register_osob(self):
        url = '/ais/servlets/WebUIServlet?fajr=A&appClassName=ais.gui.lz.LZ014App&kodAplikacie=LZ014&uiLang=SK'
        app, ops = Application.open(self.context, url)
        assert_ops(ops, 'openMainDialog', 'openDialog')

        app.open_main_dialog(*ops[0].args)
        app.open_dialog(*ops[1].args)

        return app

    def __query_dialog(self, app, meno, priezvisko, absolvent,
                       student, zamestnanec, akademicky_rok,
                       fakulta, studijny_program, uchadzaci,
                       prvy_rocnik, druhy_rocnik, treti_rocnik,
                       stvrty_rocnik, piaty_rocnik, siesty_rocnik,
                       siedmy_rocnik, osmy_rocnik, absolventi):
        rocniky = [uchadzaci, prvy_rocnik, druhy_rocnik, treti_rocnik,
                   stvrty_rocnik, piaty_rocnik, siesty_rocnik,
                   siedmy_rocnik, osmy_rocnik, absolventi]

        if any(rocniky) and not (absolvent or student or zamestnanec):
            student = True

        if studijny_program and not (absolvent or student or zamestnanec):
            absolvent = True
            student = True

        if fakulta and not (absolvent or student or zamestnanec):
            absolvent = True
            student = True
            zamestnanec = True

        app.d.absolventCheckBox.set_to(absolvent)

        app.d.studentCheckBox.set_to(student)

        app.d.zamestnanecCheckBox.set_to(zamestnanec)

        app.d.menoTextField.write(meno or '')

        app.d.priezviskoTextField.write(priezvisko or '')

        if absolvent or student or zamestnanec:
            app.d.akademickyRokComboBox.select(find_option(
                app.d.akademickyRokComboBox.options, title=akademicky_rok))

            with app.collect_operations() as ops:
                app.d.odstranitFakultuButton.click()

            if ops:
                assert_ops(ops, 'messageBox')

            if not self._select_ciselnik(app, fakulta or None, "VyberFakultaButton", "skratka"):
                return 'Fakulta nebola nájdená.'

            app.d.odstranitOdborButton.click()
            if not self._select_ciselnik(app, studijny_program or None, "VyberOdborButton", "skratka"):
                return 'Študijný program sa nenašiel, skontrolujte fakultu.'

            for index, item in enumerate(rocniky):
                if item != app.d.rocnikCheckList.items[index].checked:
                    app.d.rocnikCheckList.toggle(index)

    def vyhladaj_osobu(self, meno, priezvisko, absolvent,
                       student, zamestnanec, akademicky_rok,
                       fakulta, studijny_program, uchadzaci,
                       prvy_rocnik, druhy_rocnik, treti_rocnik,
                       stvrty_rocnik, piaty_rocnik, siesty_rocnik,
                       siedmy_rocnik, osmy_rocnik, absolventi):
        app = self._open_register_osob()

        self.__open_filter(app)

        message = self.__query_dialog(app, meno, priezvisko, absolvent,
                                      student, zamestnanec, akademicky_rok,
                                      fakulta, studijny_program, uchadzaci,
                                      prvy_rocnik, druhy_rocnik, treti_rocnik,
                                      stvrty_rocnik, piaty_rocnik, siesty_rocnik,
                                      siedmy_rocnik, osmy_rocnik, absolventi)
        if message:
            return [[], message]

        self.__close_filter(app)

        if 'email' not in app.d.osobyTable.column_map:
            self.__show_all_columns(app, app.d.osobyTable)

        while not app.d.osobyTable.is_end_of_data:
            app.d.osobyTable.scroll_down(10)
        if app.d.osobyTable.truncated:
            message = "Neboli načítané všetky dáta. Upresnite kritériá vyhľadávania."

        result = [RegOsoba(meno=row['meno'],
                           priezvisko=row['priezvisko'],
                           plne_meno=row['plneMeno'],
                           email=row['email'])
                  for row in app.d.osobyTable.loaded_rows]

        return [result, message]

    def __show_all_columns(self, app, table):
        with app.collect_operations() as ops:
            table._control_button_columns()

        app.awaited_open_dialog(ops)

        app.d.oznacitVsetkyButton.click()

        with app.collect_operations() as ops:
            app.d.enterButton.click()
        app.awaited_close_dialog(ops)

    def get_register_osob_akademicky_rok_options(self):
        app = self._open_register_osob()

        self.__open_filter(app)

        return app.d.akademickyRokComboBox.options

    def get_register_osob_fakulty(self):
        app = self._open_register_osob()

        self.__open_filter(app)

        with app.collect_operations() as ops:
            app.d.VyberFakultaButton.click()

        app.awaited_open_dialog(ops)

        fakulty = [{'id': row['skratka'], 'title': row['popis']}
                   for row in app.d.table.all_rows()]

        fakulty.insert(0, {'id': '', 'title': ''})

        with app.collect_operations() as ops:
            app.d.closeButton.click()

        app.awaited_close_dialog(ops)

        return fakulty

    def __open_filter(self, app):
        if app.d.name != "LZ015_VyhladavanieOsobFilterDlg1":
            with app.collect_operations() as ops:
                app.d.filterAction.execute()

            app.awaited_open_dialog(ops)

    def __close_filter(self, app):
        if app.d.name == "LZ015_VyhladavanieOsobFilterDlg1":
            with app.collect_operations() as ops:
                app.d.enterButton.click()

            if len(ops) > 1:
                assert_ops(ops, 'closeDialog', 'messageBox')
            else:
                assert_ops(ops, "closeDialog")

            app.close_dialog(*ops[0].args)
