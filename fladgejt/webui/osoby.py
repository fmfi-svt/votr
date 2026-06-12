from aisikl.app import Application, assert_ops
from aisikl.typeutils import ct
from fladgejt.base import BaseClient
from fladgejt.webui.commonui import WebuiCommonUIMixin
from fladgejt.webui.pool import pooled_app
from fladgejt.helpers import find_option
from fladgejt.structures import RegOsoba
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from abc import ABC
    from aisikl.app import Application
    from aisikl.components.action import Action
    from aisikl.components.button import Button
    from aisikl.components.checkbox import CheckBox
    from aisikl.components.checklist import CheckList
    from aisikl.components.combobox import ComboBox, Option
    from aisikl.components.table import Table
    from aisikl.components.textfield import TextField
    from aisikl.dialog import Dialog

    class RegisterOsobDialogsType(ABC, Dialog):
        VyberFakultaButton: Button
        absolventCheckBox: CheckBox
        akademickyRokComboBox: ComboBox
        closeButton: Button
        enterButton: Button
        filterAction: Action
        menoTextField: TextField
        odstranitFakultuButton: Button
        odstranitOdborButton: Button
        osobyTable: Table
        priezviskoTextField: TextField
        rocnikCheckList: CheckList
        studentCheckBox: CheckBox
        table: Table
        zamestnanecCheckBox: CheckBox
else:
    RegisterOsobDialogsType = None


class WebuiOsobyMixin(WebuiCommonUIMixin, BaseClient):
    @pooled_app
    def _open_register_osob(self) -> Application[RegisterOsobDialogsType]:
        url = '/ais/servlets/WebUIServlet?fajr=A&appClassName=ais.gui.lz.LZ014App&kodAplikacie=LZ014&uiLang=SK'
        app, ops = Application[RegisterOsobDialogsType].open(self.context, url)
        assert_ops(ops, 'openMainDialog', 'openDialog')

        app.open_main_dialog(*ops[0].args)
        app.open_dialog(*ops[1].args)

        return app

    def __query_dialog(self, app: Application[RegisterOsobDialogsType], meno: str | None, priezvisko: str | None, absolvent: bool,
                       student: bool, zamestnanec: bool, akademicky_rok: str,
                       fakulta: str | None, studijny_program: str | None, uchadzaci: bool,
                       prvy_rocnik: bool, druhy_rocnik: bool, treti_rocnik: bool,
                       stvrty_rocnik: bool, piaty_rocnik: bool, siesty_rocnik: bool,
                       siedmy_rocnik: bool, osmy_rocnik: bool, absolventi: bool) -> str | None:
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
                assert_ops(ops, 'messageBox')   # "Interna chyba: Nepodarilo sa osetrenie udalosti."

            if not self._select_ciselnik(app, fakulta or None, "VyberFakultaButton", "skratka"):
                return 'Fakulta nebola nájdená.'

            app.d.odstranitOdborButton.click()
            if not self._select_ciselnik(app, studijny_program or None, "VyberOdborButton", "skratka"):
                return 'Študijný program sa nenašiel, skontrolujte fakultu.'

            for index, item in enumerate(rocniky):
                if item != app.d.rocnikCheckList.items[index].checked:
                    app.d.rocnikCheckList.toggle(index)

    def vyhladaj_osobu(self, meno: str | None, priezvisko: str | None, absolvent: bool,
                       student: bool, zamestnanec: bool, akademicky_rok: str,
                       fakulta: str | None, studijny_program: str | None, uchadzaci: bool,
                       prvy_rocnik: bool, druhy_rocnik: bool, treti_rocnik: bool,
                       stvrty_rocnik: bool, piaty_rocnik: bool, siesty_rocnik: bool,
                       siedmy_rocnik: bool, osmy_rocnik: bool, absolventi: bool) -> tuple[list[RegOsoba], str | None]:
        app = self._open_register_osob()

        self.__open_filter(app)

        message = self.__query_dialog(app, meno, priezvisko, absolvent,
                                      student, zamestnanec, akademicky_rok,
                                      fakulta, studijny_program, uchadzaci,
                                      prvy_rocnik, druhy_rocnik, treti_rocnik,
                                      stvrty_rocnik, piaty_rocnik, siesty_rocnik,
                                      siedmy_rocnik, osmy_rocnik, absolventi)
        if message:
            return ([], message)

        self.__close_filter(app)

        if 'email' not in app.d.osobyTable.column_map:
            self._show_all_columns(app, app.d.osobyTable)

        while not app.d.osobyTable.is_end_of_data:
            app.d.osobyTable.scroll_down(10)
        if app.d.osobyTable.truncated:
            message = "Neboli načítané všetky dáta. Upresnite kritériá vyhľadávania."

        result = [RegOsoba(meno=row['meno'],
                           priezvisko=row['priezvisko'],
                           plne_meno=row['plneMeno'],
                           email=row['email'])
                  for row in app.d.osobyTable.loaded_rows]

        return (result, message)

    def get_register_osob_akademicky_rok_options(self) -> list[Option]:
        app = self._open_register_osob()

        self.__open_filter(app)

        return app.d.akademickyRokComboBox.options

    def get_register_osob_fakulty(self) -> list[dict[str, str]]:
        app = self._open_register_osob()

        self.__open_filter(app)

        with app.collect_operations() as ops:
            app.d.VyberFakultaButton.click()

        app.awaited_open_dialog(ops)

        fakulty = [{'id': ct(str, row['skratka']), 'title': ct(str, row['popis'])}
                   for row in app.d.table.all_rows()]

        fakulty.insert(0, {'id': '', 'title': ''})

        with app.collect_operations() as ops:
            app.d.closeButton.click()

        app.awaited_close_dialog(ops)

        return fakulty

    def __open_filter(self, app: Application[RegisterOsobDialogsType]) -> None:
        if app.d.name != "LZ015_VyhladavanieOsobFilterDlg1":
            with app.collect_operations() as ops:
                app.d.filterAction.execute()

            app.awaited_open_dialog(ops)

    def __close_filter(self, app: Application[RegisterOsobDialogsType]) -> None:
        if app.d.name == "LZ015_VyhladavanieOsobFilterDlg1":
            with app.collect_operations() as ops:
                app.d.enterButton.click()

            app.awaited_close_dialog(ops)
