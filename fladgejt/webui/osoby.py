from aisikl.app import Application
from aisikl.operations import CloseDialogOp, MessageBoxOp, OpenDialogOp
from fladgejt.base import BaseClient
from fladgejt.webui.commonui import select_ciselnik, show_all_columns
from fladgejt.webui.pool import pooled_app
from fladgejt.helpers import find_option
from fladgejt.structures import RegOsoba
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from abc import ABC
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
        VyberOdborButton: Button
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


class WebuiOsobyMixin(BaseClient):
    @pooled_app
    async def _open_register_osob(self) -> Application[RegisterOsobDialogsType]:
        url = '/ais/servlets/WebUIServlet?fajr=A&appClassName=ais.gui.lz.LZ014App&kodAplikacie=LZ014&uiLang=SK'
        app, ops = await Application[RegisterOsobDialogsType].open(self.context, url)
        op1, op2 = ops.expect_two(OpenDialogOp, OpenDialogOp)
        await op1.perform()
        await op2.perform()

        return app

    async def __query_dialog(self, app: Application[RegisterOsobDialogsType], meno: str | None, priezvisko: str | None, absolvent: bool,
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

        await app.d.absolventCheckBox.set_to(absolvent)

        await app.d.studentCheckBox.set_to(student)

        await app.d.zamestnanecCheckBox.set_to(zamestnanec)

        await app.d.menoTextField.write(meno or '')

        await app.d.priezviskoTextField.write(priezvisko or '')

        if absolvent or student or zamestnanec:
            await app.d.akademickyRokComboBox.select(find_option(
                app.d.akademickyRokComboBox.options, title=akademicky_rok))

            ops = await app.d.odstranitFakultuButton.click(return_ops=True)
            if ops:
                ops.expect_one(MessageBoxOp)   # "Interna chyba: Nepodarilo sa osetrenie udalosti."

            if not await select_ciselnik(app, fakulta or None, app.d.VyberFakultaButton, "skratka"):
                return 'Fakulta nebola nájdená.'

            await app.d.odstranitOdborButton.click()
            if not await select_ciselnik(app, studijny_program or None, app.d.VyberOdborButton, "skratka"):
                return 'Študijný program sa nenašiel, skontrolujte fakultu.'

            for index, item in enumerate(rocniky):
                if item != app.d.rocnikCheckList.items[index].checked:
                    await app.d.rocnikCheckList.toggle(index)

    async def vyhladaj_osobu(self, meno: str | None, priezvisko: str | None, absolvent: bool,
                       student: bool, zamestnanec: bool, akademicky_rok: str,
                       fakulta: str | None, studijny_program: str | None, uchadzaci: bool,
                       prvy_rocnik: bool, druhy_rocnik: bool, treti_rocnik: bool,
                       stvrty_rocnik: bool, piaty_rocnik: bool, siesty_rocnik: bool,
                       siedmy_rocnik: bool, osmy_rocnik: bool, absolventi: bool) -> tuple[list[RegOsoba], str | None]:
        app = await self._open_register_osob()

        await self.__open_filter(app)

        message = await self.__query_dialog(
            app, meno, priezvisko, absolvent, student, zamestnanec,
            akademicky_rok, fakulta, studijny_program, uchadzaci, prvy_rocnik,
            druhy_rocnik, treti_rocnik, stvrty_rocnik, piaty_rocnik,
            siesty_rocnik, siedmy_rocnik, osmy_rocnik, absolventi)
        if message:
            return ([], message)

        await self.__close_filter(app)

        if 'email' not in app.d.osobyTable.column_map:
            await show_all_columns(app, app.d.osobyTable)

        while not app.d.osobyTable.is_end_of_data:
            await app.d.osobyTable.scroll_down(10)
        if app.d.osobyTable.truncated:
            message = "Neboli načítané všetky dáta. Upresnite kritériá vyhľadávania."

        result = [RegOsoba(meno=row['meno'],
                           priezvisko=row['priezvisko'],
                           plne_meno=row['plneMeno'],
                           email=row['email'])
                  for row in app.d.osobyTable.loaded_rows]

        return (result, message)

    async def get_register_osob_akademicky_rok_options(self) -> list[Option]:
        app = await self._open_register_osob()

        await self.__open_filter(app)

        return app.d.akademickyRokComboBox.options

    async def get_register_osob_fakulty(self) -> list[dict[str, str]]:
        app = await self._open_register_osob()

        await self.__open_filter(app)

        ops = await app.d.VyberFakultaButton.click(return_ops=True)
        await ops.expect_one(OpenDialogOp).perform()

        fakulty = [{'id': row['skratka'], 'title': row['popis']}
                   for row in await app.d.table.all_rows()]

        fakulty.insert(0, {'id': '', 'title': ''})

        ops = await app.d.closeButton.click(return_ops=True)
        await ops.expect_one(CloseDialogOp).perform()

        return fakulty

    async def __open_filter(self, app: Application[RegisterOsobDialogsType]) -> None:
        if app.d.name != "LZ015_VyhladavanieOsobFilterDlg1":
            ops = await app.d.filterAction.execute(return_ops=True)
            await ops.expect_one(OpenDialogOp).perform()

    async def __close_filter(self, app: Application[RegisterOsobDialogsType]) -> None:
        if app.d.name == "LZ015_VyhladavanieOsobFilterDlg1":
            ops = await app.d.enterButton.click(return_ops=True)
            await ops.expect_one(CloseDialogOp).perform()
