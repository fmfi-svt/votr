#!/usr/bin/env python3

"""Opens the only AIS application which allows anonymous access, and clicks
around in it. Can be used to test Votr without an account, and verify that
Aisikl is still able to parse common AIS GUI components.
"""

from aisikl.app import Application
from fladgejt.helpers import find_option
from tests.testutils import scenario_main
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from abc import ABC
    from aisikl.components.button import Button
    from aisikl.components.combobox import ComboBox
    from aisikl.components.menuitem import MenuItem
    from aisikl.components.table import Table
    from aisikl.dialog import Dialog
    from fladgejt.base import BaseClient

    class TestDialogsType(ABC, Dialog):
        enterButton: Button
        fakultaComboBox: ComboBox
        oznacitInverzneButton: Button
        oznacitVsetkyButton: Button
        resetButton: Button
        studPlanMenuItem: MenuItem
        studijneProgramyTable: Table
        vyberButton: Button
        zobrazitPreFakultuButton: Button
        zobrazitPreStudiumButton: Button
else:
    TestDialogsType = None

async def run(client: BaseClient) -> None:
    # 1. "VSST060 - Register predmetov" doesn't allow anonymous access anymore.

    # 2. "VSST178 - Študijné plány, informačné listy, ... študijných programov"

    app, ops = await Application[TestDialogsType].open(client.context, '/ais/servlets/WebUIServlet?appClassName=ais.gui.vs.st.VSST178App&kodAplikacie=VSST178&uiLang=SK')
    await app.awaited_open_main_dialog(ops)

    await app.d.fakultaComboBox.select(find_option(
        app.d.fakultaComboBox.options, id='FMFI'))
    await app.d.zobrazitPreFakultuButton.click()
    await app.d.fakultaComboBox.select(find_option(
        app.d.fakultaComboBox.options, id='UK'))
    await app.d.zobrazitPreFakultuButton.click()
    await app.d.zobrazitPreStudiumButton.click()

    with app.collect_operations() as ops:
        await app.d.studPlanMenuItem.click()
    with app.collect_operations() as ops2:
        await app.awaited_abort_box(ops)
    await app.awaited_shell_exec(ops2)

    with app.collect_operations() as ops:
        await app.d.studijneProgramyTable.control_button_columns()
    await app.awaited_open_dialog(ops)

    await app.d.oznacitInverzneButton.click()
    await app.d.oznacitVsetkyButton.click()

    with app.collect_operations() as ops:
        await app.d.enterButton.click()
    await app.awaited_close_dialog(ops)

    with app.collect_operations() as ops:
        await app.d.studijneProgramyTable.control_button_sort()
    await app.awaited_open_dialog(ops)

    await app.d.resetButton.click()

    with app.collect_operations() as ops:
        await app.d.vyberButton.click()
    with app.collect_operations() as ops2:
        await app.awaited_abort_box(ops)
    await app.awaited_close_dialog(ops2)

    # TODO: Clicking obsahNaplnMenuItem leads to unexplored territory.
    # It executes a new script line: `webui().sendEmptyRequest(true); return;`
    # and uses the progressBar component type.
    # Same if you open infoListyMenuItem and click enterButton in that dialog,
    # which also uses progressBar.setMaximum().

if __name__ == '__main__':
    scenario_main(run, anonymous=True)
