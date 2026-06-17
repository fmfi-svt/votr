from aisikl.app import Application, assert_ops
from aisikl.exceptions import AISBehaviorError
from fladgejt.helpers import find_row_insensitive
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from abc import ABC
    from aisikl.components.button import Button
    from aisikl.components.table import Table
    from aisikl.dialog import Dialog

    class CiselnikDialogsType(ABC, Dialog):
        closeButton: Button
        enterButton: Button
        table: Table

    class ShowColumnsDialogsType(ABC, Dialog):
        enterButton: Button
        table: Table
else:
    CiselnikDialogsType = None
    ShowColumnsDialogsType = None


class WebuiCommonUIMixin:
    def _select_ciselnik[D](self, app_arg: Application[D], text: str | None, select_button: str, compare_column: str) -> bool:
        app = cast(Application[CiselnikDialogsType], app_arg)
        # Ciselnik typu SSSC001
        if text is not None:
            old_ignored_messages = app.ignored_messages
            app.ignored_messages = [m for m in app.ignored_messages if m != 'Podmienkam nevyhovuje žiadny záznam.']
            try:
                with app.collect_operations() as ops:
                    app.d.components[select_button].click()  # pyrefly: ignore [missing-attribute] # pyright: ignore [reportAttributeAccessIssue, reportUnknownMemberType]
            finally:
                app.ignored_messages = old_ignored_messages

            if ops:
                if len(ops) == 1 and ops[0].method == 'messageBox' and ops[0].args[0] == 'Podmienkam nevyhovuje žiadny záznam.':
                    return False

                assert_ops(ops, 'openDialog')

                if ops[0].args[0]['code'] != 'SSSC001':
                    raise AISBehaviorError(f"AIS opened an unexpected dialog: {ops}")

                app.awaited_open_dialog(ops)
                try:
                    index = find_row_insensitive(app.d.table.all_rows(), **{compare_column: text})
                except KeyError:
                    with app.collect_operations() as ops:
                        app.d.closeButton.click()

                    app.awaited_close_dialog(ops)

                    return False
                else:
                    app.d.table.select(index)

                    with app.collect_operations() as ops:
                        app.d.enterButton.click()

                    app.awaited_close_dialog(ops)

        return True

    def _select_text_ciselnik[D: Dialog](self, app: Application[D], text: str | None, text_field: str, delete_button: str, select_button: str, compare_column: str) -> bool:
        if not app.d.components[text_field].is_editable():  # pyrefly: ignore [missing-attribute] # pyright: ignore [reportAttributeAccessIssue, reportUnknownMemberType]
            app.d.components[delete_button].click()  # pyrefly: ignore [missing-attribute] # pyright: ignore [reportAttributeAccessIssue, reportUnknownMemberType]
        app.d.components[text_field].write(text or '')  # pyrefly: ignore [missing-attribute] # pyright: ignore [reportAttributeAccessIssue, reportUnknownMemberType]

        return self._select_ciselnik(app, text, select_button, compare_column)

    def _show_all_columns[D](self, app_arg: Application[D], table: Table) -> None:
        app = cast(Application[ShowColumnsDialogsType], app_arg)
        with app.collect_operations() as ops:
            table.control_button_columns()

        app.awaited_open_dialog(ops)

        for row in app.d.table.all_rows():
            if row.cell('check').value == False:
                app.d.table.edit_cell('check', row.id, True)

        with app.collect_operations() as ops:
            app.d.enterButton.click()
        app.awaited_close_dialog(ops)
