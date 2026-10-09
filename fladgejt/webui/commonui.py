from aisikl.app import assert_ops
from aisikl.exceptions import AISBehaviorError
from fladgejt.helpers import find_row_insensitive
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from abc import ABC
    from aisikl.app import Application
    from aisikl.components.button import Button
    from aisikl.components.table import Table
    from aisikl.components.textfield import TextField
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


async def select_ciselnik[D: Dialog](app_arg: Application[D], text: str | None, select_button: Button, compare_column: str) -> bool:
    app = cast('Application[CiselnikDialogsType]', app_arg)
    # Ciselnik typu SSSC001

    if text is None:
        return True

    old_ignored_messages = app.ignored_messages
    app.ignored_messages = [m for m in app.ignored_messages if m != 'Podmienkam nevyhovuje žiadny záznam.']
    try:
        with app.collect_operations() as ops:
            await select_button.click()
    finally:
        app.ignored_messages = old_ignored_messages

    # Ak nevyskoci ani chyba ani dialog, asi to znamena, ze AIS nasiel presne
    # jeden riadok s prefixom `text`. Moze ale nemusi to byt presna zhoda.
    # Priklad: register predmetov, daj studijny program "AI" -> doplni sa "AIN".
    if not ops:
        return True

    # Ak AIS nenasiel ziaden riadok s danym prefixom.
    if len(ops) == 1 and ops[0].method == 'messageBox' and ops[0].args[0] == 'Podmienkam nevyhovuje žiadny záznam.':
        return False

    # Ak AIS nasiel viacero riadkov s danym prefixom.
    assert_ops(ops, 'openDialog')

    if ops[0].args[0]['code'] != 'SSSC001':
        raise AISBehaviorError(f"AIS opened an unexpected dialog: {ops}")

    await app.awaited_open_dialog(ops)
    try:
        index = find_row_insensitive(await app.d.table.all_rows(), **{compare_column: text})
    except KeyError:
        with app.collect_operations() as ops:
            await app.d.closeButton.click()

        await app.awaited_close_dialog(ops)

        return False

    await app.d.table.select(index)

    with app.collect_operations() as ops:
        await app.d.enterButton.click()

    await app.awaited_close_dialog(ops)

    return True

async def select_text_ciselnik[D: Dialog](app: Application[D], text: str | None, text_field: TextField, delete_button: Button, select_button: Button, compare_column: str) -> bool:
    if not text_field.is_editable():
        await delete_button.click()
    await text_field.write(text or '')

    return await select_ciselnik(app, text, select_button, compare_column)

async def show_all_columns[D](app_arg: Application[D], table: Table) -> None:
    app = cast('Application[ShowColumnsDialogsType]', app_arg)
    with app.collect_operations() as ops:
        await table.control_button_columns()

    await app.awaited_open_dialog(ops)

    for row in await app.d.table.all_rows():
        if row.cell('check').value == False:
            await app.d.table.edit_cell('check', row.id, True)

    with app.collect_operations() as ops:
        await app.d.enterButton.click()
    await app.awaited_close_dialog(ops)
