from aisikl.app import assert_ops
from fladgejt.helpers import find_row_insensitive


class WebuiCommonUIMixin:
    def _select_ciselnik(self, app, text, select_button, compare_column):
        # Ciselnik typu SSSC001
        if text is not None:
            old_ignored_messages = app.ignored_messages
            app.ignored_messages = [m for m in app.ignored_messages if m != 'Podmienkam nevyhovuje žiadny záznam.']
            try:
                with app.collect_operations() as ops:
                    app.d.components[select_button].click()
            finally:
                app.ignored_messages = old_ignored_messages

            if ops:
                if len(ops) == 1 and ops[0].method == 'messageBox' and ops[0].args[0] == 'Podmienkam nevyhovuje žiadny záznam.':
                    return False

                assert_ops(ops, 'openDialog')

                if ops[0].args[2] != 'SSSC001':
                    raise AISBehaviorError("AIS opened an unexpected dialog: {}".format(ops))

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

    def _select_text_ciselnik(self, app, text, text_field, delete_button, select_button, compare_column):
        if not app.d.components[text_field].is_editable():
            app.d.components[delete_button].click()
        app.d.components[text_field].write(text or '')

        return self._select_ciselnik(app, text, select_button, compare_column)

    def _show_all_columns(self, app, table):
        with app.collect_operations() as ops:
            table._control_button_columns()

        app.awaited_open_dialog(ops)

        for row in app.d.table.all_rows():
            if row['check'] == False:
                app.d.table.edit_cell('check', row.id, True)

        with app.collect_operations() as ops:
            app.d.enterButton.click()
        app.awaited_close_dialog(ops)
