from aisikl.app import assert_ops
from aisikl.exceptions import AISBehaviorError, AmbiguousItemError, NotFoundError


def _normal_eq(a, b):
    return a == b

def _insensitive_eq(a, b):
    return a.casefold() == b.casefold()


class WebuiCommonUIMixin:
    def _find_row(self, rows, case_insensitive=False, allow_ambiguous=False, **conditions):
        '''Searches the list of rows for one that matches all given
        conditions. Returns the index of the matching row.

        :param rows: List of table rows.
        :param case_insensitive: Ignore letter case in string comparisons.
        :param allow_ambiguous: Allow multiple matching rows and just return
            the first one. If False (default), multiple matching rows will
            raise an error.
        :param \*\*conditions: Key-value pairs which must exist in the row. If
            conditions contains an item ``'foo': 'bar'``, that means we're
            looking for rows that have ``row['foo'] == 'bar'``.
        Returns:
            The index of the row that matches all conditions.
        Raises:
            KeyNotFoundError: Raised if no such row is found.
            AmbiguousKeyError: Raised if allow_ambigous is False and multiple
                matching rows were found.
        '''
        eq = _insensitive_eq if case_insensitive else _normal_eq
        found = [
            index
            for index, row in enumerate(rows)
            if all(eq(row[key], value) for key, value in conditions.items())
        ]
        if not found:
            raise NotFoundError("Row not found: {!r}".format(conditions))
        if len(found) > 1:
            if allow_ambiguous:
                self.context.log('ambiguous', "{} rows match".format(len(found)), conditions)
            else:
                raise AmbiguousItemError("{} rows match {!r}".format(len(found), conditions))
        return found[0]

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

                if ops[0].args[0]['code'] != 'SSSC001':
                    raise AISBehaviorError("AIS opened an unexpected dialog: {}".format(ops))

                app.awaited_open_dialog(ops)
                try:
                    index = self._find_row(app.d.table.all_rows(), case_insensitive=True, **{compare_column: text})
                except NotFoundError:
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
