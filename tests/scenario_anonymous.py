"""Opens the only AIS application which allows anonymous access, and clicks
around in it. Can be used to test Votr without an account, and verify that
Aisikl is still able to parse common AIS GUI components.
"""

from aisikl.app import Application
from fladgejt.helpers import find_option
from tests.testutils import scenario_main

def run(client):
    # 1. "VSST060 - Register predmetov" doesn't allow anonymous access anymore.

    # 2. "VSST178 - Študijné plány, informačné listy, ... študijných programov"

    app, ops = Application.open(client.context, '/ais/servlets/WebUIServlet?appClassName=ais.gui.vs.st.VSST178App&kodAplikacie=VSST178&uiLang=SK')
    app.awaited_open_main_dialog(ops)

    app.d.fakultaComboBox.select(find_option(
        app.d.fakultaComboBox.options, id='FMFI'))
    app.d.zobrazitPreFakultuButton.click()
    app.d.fakultaComboBox.select(find_option(
        app.d.fakultaComboBox.options, id='UK'))
    app.d.zobrazitPreFakultuButton.click()
    app.d.zobrazitPreStudiumButton.click()

    with app.collect_operations() as ops:
        app.d.studPlanMenuItem.click()
    with app.collect_operations() as ops2:
        app.awaited_abort_box(ops)
    app.awaited_shell_exec(ops2)

    with app.collect_operations() as ops:
        app.d.studijneProgramyTable.control_button_columns()
    app.awaited_open_dialog(ops)

    app.d.oznacitInverzneButton.click()
    app.d.oznacitVsetkyButton.click()

    with app.collect_operations() as ops:
        app.d.enterButton.click()
    app.awaited_close_dialog(ops)

    with app.collect_operations() as ops:
        app.d.studijneProgramyTable.control_button_sort()
    app.awaited_open_dialog(ops)

    app.d.resetButton.click()

    with app.collect_operations() as ops:
        app.d.vyberButton.click()
    with app.collect_operations() as ops2:
        app.awaited_abort_box(ops)
    app.awaited_close_dialog(ops2)

    # TODO: Clicking obsahNaplnMenuItem leads to unexplored territory.
    # It executes a new script line: `webui().sendEmptyRequest(true); return;`
    # and uses the progressBar component type.
    # Same if you open infoListyMenuItem and click enterButton in that dialog,
    # which also uses progressBar.setMaximum().

if __name__ == '__main__':
    scenario_main(run, anonymous=True)
