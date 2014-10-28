from aisikl.app import assert_ops
from fladgejt.helpers import find_row


# Ciselnik typu SSSC001
class WebuiCiselnikMixin:
    def _select_ciselnik(self, app, text, text_field, erase_button, select_action, compare_column):
        if text is not None:
            if not app.d.components[text_field].is_editable():
                app.d.components[erase_button].click()

            app.d.components[text_field].write(text)

            with app.collect_operations() as ops:
                app.d.components[select_action].execute()

            if ops:
                assert_ops(ops, 'openDialog')

                if ops[0].args[2] != 'SSSC001':
                    raise AISBehaviorError("AIS opened an unexpected dialog: {}".format(ops))

                app.awaited_open_dialog(ops)
                try:
                    index = find_row(app.d.table.all_rows(), **{compare_column: text})
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
        else:
            if app.d.components[text_field].is_editable():
                app.d.components[text_field].write('')
            else:
                app.d.components[erase_button].click()

        return True
