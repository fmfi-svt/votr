from aisikl.app import Application, assert_ops
import base64
from fladgejt.base import BaseClient
from fladgejt.webui.commonui import WebuiCommonUIMixin
from fladgejt.webui.pool import pooled_app
from fladgejt.helpers import find_option, find_row, decode_key
from fladgejt.structures import RegUcitelPredmetu, PrihlasenyStudent, RegPredmet
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from abc import ABC
    from aisikl.components.action import Action
    from aisikl.components.button import Button
    from aisikl.components.combobox import ComboBox, Option
    from aisikl.components.menuitem import MenuItem
    from aisikl.components.numbercontrol import NumberControl
    from aisikl.components.table import Table
    from aisikl.components.textfield import TextField
    from aisikl.dialog import Dialog

    class RegisterPredmetovDialogsType(ABC, Dialog):
        akRokComboBox: ComboBox
        cisloPredmetuNumberControl: NumberControl
        closeButton: Button
        enterButton: Button
        fakultaUniverzitaComboBox: ComboBox
        infListMenuItem: MenuItem
        nazovPredmetuTextField: TextField
        odobratVyucujucehoButton: Button
        sablonyTable: Table
        semesterComboBox: ComboBox
        skratkaPredmetuTextField: TextField
        stupenPredmetuComboBox: ComboBox
        typPredmetuComboBox: ComboBox
        vyucujuciTextField: TextField
        zaradeniStudentiTable: Table
        zobrazitLenComboBox: ComboBox
        zobrazitPredmetyButton: Button
        zoznamPredmetovTable: Table
        zoznamStudentovAction: Action

    class NastenkaPredmetuDialogsType(ABC, Dialog):
        fakultaComboBox: ComboBox
        nacitatPredmetyButton: Button
        potvrditOrgJednotkuButton: Button
        rokComboBox: ComboBox
        semesterComboBox: ComboBox
        skratkaTextField: TextField
        skupinaPredmetovTable: Table
        vyucujuciTable: Table
        zobrazitComboBox: ComboBox
else:
    RegisterPredmetovDialogsType = None
    NastenkaPredmetuDialogsType = None

class GetStudentiZapisaniNaPredmetResult(TypedDict):
    items: list[PrihlasenyStudent]
    message: str | None
    predmet: RegPredmet | None


class WebuiPredmetyMixin(WebuiCommonUIMixin, BaseClient):
    @pooled_app
    async def _open_register_predmetov(self) -> Application[RegisterPredmetovDialogsType]:
        url = '/ais/servlets/WebUIServlet?fajr=A&appClassName=ais.gui.vs.st.VSST060App&kodAplikacie=VSST060&uiLang=SK'
        app, ops = await Application[RegisterPredmetovDialogsType].open(self.context, url)
        await app.awaited_open_main_dialog(ops)
        return app

    async def get_informacny_list(self, kod_predmetu: str, akademicky_rok: str) -> str | None:
        app = await self._open_register_predmetov()

        stredisko, _, zvysok = decode_key(kod_predmetu)[0].partition('/')
        skratka = zvysok.rpartition('/')[0]

        # Napiseme stredisko a skratku predmetu.
        await self.__query_dialog(app, akademicky_rok, stredisko=stredisko,
            skratka_predmetu=skratka)

        # Stlacime nacitavaci button (sipku dole).
        await app.d.zobrazitPredmetyButton.click()

        if not app.d.zoznamPredmetovTable.loaded_rows:
            return None
        # TODO: zdokumentovat, ze ak matchuju viacere informacne listy, je
        # undefined behavior ktory vratime. (asi vzdy ten prvy, ale kto vie ako
        # ich AIS zoradi.)

        # Stlacime v menu "Informacny list".
        with app.collect_operations() as ops:
            await app.d.infListMenuItem.click()

        # Otvori sa dialog na vyber formatu.
        await app.awaited_open_dialog(ops)

        # Vyberieme vrchny riadok. TODO: fakt chceme ten?
        await app.d.sablonyTable.select(0)

        # Stlacime OK.
        with app.collect_operations() as ops:
            await app.d.enterButton.click()

        # Dialog sa zavrie a otvori sa "prosim cakajte", tak cakame.
        assert_ops(ops, 'closeDialog', 'abortBox')
        await app.close_dialog(*ops[0].args)
        with app.collect_operations() as ops2:
            await app.abort_box(*ops[1].args)

        # Vratime zakodove PDF.
        url = await app.awaited_shell_exec(ops2)
        return base64.b64encode(url.content).decode()

    async def __query_dialog(self, app: Application[RegisterPredmetovDialogsType], akademicky_rok: str, fakulta: str | None=None, semester: str | None=None,
                       stupen_predmetu: str | None=None, typ_predmetu: str | None=None,
                       zobrazit_len: str | None=None, skratka_predmetu: str | None=None,
                       nazov_predmetu: str | None=None, cislo_predmetu: str | None=None,
                       stredisko: str | None=None, skratka_sp: str | None=None) -> str | None:
        message: list[str] = []

        await app.d.fakultaUniverzitaComboBox.select(find_option(app.d.fakultaUniverzitaComboBox.options, id=(fakulta or '')))

        await app.d.semesterComboBox.select(find_option(app.d.semesterComboBox.options, id=(semester or '')))

        await app.d.stupenPredmetuComboBox.select(find_option(app.d.stupenPredmetuComboBox.options, id=(stupen_predmetu or '')))

        await app.d.typPredmetuComboBox.select(find_option(app.d.typPredmetuComboBox.options, id=(typ_predmetu or '')))

        await app.d.zobrazitLenComboBox.select(find_option(app.d.zobrazitLenComboBox.options, id=(zobrazit_len or '')))

        await app.d.skratkaPredmetuTextField.write(skratka_predmetu or '')

        await app.d.nazovPredmetuTextField.write(nazov_predmetu or '')

        await app.d.cisloPredmetuNumberControl.write(cislo_predmetu or '')

        if not await self._select_text_ciselnik(
                app, stredisko, 'skratkaStrediskaTextField',
                'zmazatStrediskoButton', 'vybratStrediskoButton', 'skratka'):
            message.append("Stredisko neexistuje.")

        if not await self._select_text_ciselnik(
                app, skratka_sp, 'skratkaStudProgramuTextField',
                'zmazatStudProgramButton', 'vybratStudProogramButton',
                'skratka'):
            message.append("Študijný program neexistuje.")

        if app.d.vyucujuciTextField.value:
            await app.d.odobratVyucujucehoButton.click()

        await app.d.akRokComboBox.select(
            find_option(app.d.akRokComboBox.options, id=akademicky_rok))

        return ' '.join(message) or None

    async def get_studenti_zapisani_na_predmet(self, predmet_key: str, akademicky_rok: str) -> GetStudentiZapisaniNaPredmetResult:
        (skratka_predmetu,) = decode_key(predmet_key)
        app = await self._open_register_predmetov()

        await self.__query_dialog(app, akademicky_rok, skratka_predmetu='/'.join(skratka_predmetu.split('/')[1:-1]))

        await app.d.zobrazitPredmetyButton.click()

        if not await app.d.zoznamPredmetovTable.all_rows():
            # predmet nebol najdeny (napriklad uz je prilis stary ale napriek
            # tomu ho mam v mojom hodnoteni)
            return GetStudentiZapisaniNaPredmetResult(items=[], message=None, predmet=None)

        predmet_index = find_row(await app.d.zoznamPredmetovTable.all_rows(), skratka=skratka_predmetu)
        await app.d.zoznamPredmetovTable.select(predmet_index)

        predmet_row = (await app.d.zoznamPredmetovTable.all_rows())[predmet_index]
        predmet = RegPredmet(skratka=predmet_row['skratka'],
                             nazov=predmet_row['nazov'],
                             semester=predmet_row['kodSemester'],
                             stredisko=predmet_row['stredisko'],
                             fakulta=predmet_row['FakUniv'],
                             rozsah_vyucby=predmet_row['rozsah'],
                             konanie=predmet_row['konanie'],
                             cudzi_nazov=predmet_row['nazovJ'],
                             kredit=predmet_row['kredit'])
        with app.collect_operations() as ops:
            await app.d.zoznamStudentovAction.execute()

        if len(ops) == 1 and ops[0].method == 'messageBox':
            return GetStudentiZapisaniNaPredmetResult(items=[], message=ops[0].args[0], predmet=predmet)

        await app.awaited_open_dialog(ops)

        studenti = [PrihlasenyStudent(sp_skratka=row['studProgSkratka'],
                                      datum_prihlasenia=row['datumZapisania'],
                                      plne_meno=row['plneMeno'],
                                      rocnik=row['rokRocnik'],
                                      email=row['email'])
                    for row in await app.d.zaradeniStudentiTable.all_rows()]

        # zatvarame dialog so zoznamom studentov
        with app.collect_operations() as ops:
            await app.d.closeButton.click()

        await app.awaited_close_dialog(ops)

        return GetStudentiZapisaniNaPredmetResult(items=studenti, message=None, predmet=predmet)

    @pooled_app
    async def _open_nastenka_predmetu(self) -> Application[NastenkaPredmetuDialogsType]:
        url = '/ais/servlets/WebUIServlet?fajr=A&appClassName=ais.gui.vs.st.VSST157App&kodAplikacie=VSST157&uiLang=SK'
        app, ops = await Application[NastenkaPredmetuDialogsType].open(self.context, url)
        await app.awaited_open_main_dialog(ops)
        return app

    async def get_ucitelia_predmetu(self, predmet_key: str, akademicky_rok: str, semester: str, fakulty: str) -> list[RegUcitelPredmetu]:
        (skratka_predmetu,) = decode_key(predmet_key)

        app = await self._open_nastenka_predmetu()

        fakulta = fakulty.split(',')[0]
        fakulta_index = find_option(app.d.fakultaComboBox.options, id=fakulta)
        if app.d.fakultaComboBox.selected_index != fakulta_index:
            await app.d.fakultaComboBox.select(fakulta_index)
            await app.d.potvrditOrgJednotkuButton.click()

        akademicky_rok_index = find_option(app.d.rokComboBox.options, title=akademicky_rok)
        if app.d.rokComboBox.selected_index != akademicky_rok_index:
            await app.d.rokComboBox.select(akademicky_rok_index)

        await app.d.skratkaTextField.write(skratka_predmetu)

        # nastavime zobrazenie vsetkych predmetov, nie len tych co
        # mame zapisane.
        zobrazit_index = find_option(app.d.zobrazitComboBox.options, id="VSETKY")
        if app.d.zobrazitComboBox.selected_index != zobrazit_index:
            await app.d.zobrazitComboBox.select(zobrazit_index)

        mozne_semestre = [semester] if semester else ["Z", "L"]
        for semester in mozne_semestre:
            semester_index = find_option(app.d.semesterComboBox.options, id=semester)
            if app.d.semesterComboBox.selected_index != semester_index:
                await app.d.semesterComboBox.select(semester_index)

            await app.d.nacitatPredmetyButton.click()

            if await app.d.skupinaPredmetovTable.all_rows():
                await app.d.skupinaPredmetovTable.select(
                    find_row(await app.d.skupinaPredmetovTable.all_rows(), skratka=skratka_predmetu))

                ucitelia = [RegUcitelPredmetu(plne_meno=row['plneMeno'],
                                              typ=row['typVyucujuceho'])
                            for row in await app.d.vyucujuciTable.all_rows()]
                return ucitelia

        return []

    async def vyhladaj_predmety(self, akademicky_rok: str, fakulta: str | None, stredisko: str | None, skratka_sp: str | None,
                          skratka_predmetu: str | None, nazov_predmetu: str | None, semester: str | None, stupen: str | None) -> tuple[list[RegPredmet], str | None]:
        app = await self._open_register_predmetov()

        message = await self.__query_dialog(app,
                                      akademicky_rok,
                                      fakulta=fakulta,
                                      semester=semester,
                                      stupen_predmetu=stupen,
                                      skratka_predmetu=skratka_predmetu,
                                      nazov_predmetu=nazov_predmetu,
                                      stredisko=stredisko,
                                      skratka_sp=skratka_sp)

        if message:
            return ([], message)

        await app.d.zobrazitPredmetyButton.click()

        while not app.d.zoznamPredmetovTable.is_end_of_data:
            await app.d.zoznamPredmetovTable.scroll_down(10)
        if app.d.zoznamPredmetovTable.truncated:
            message = "Neboli načítané všetky dáta. Upresnite kritériá vyhľadávania."

        predmety = [RegPredmet(skratka=row['skratka'],
                               nazov=row['nazov'],
                               semester=row['kodSemester'],
                               stredisko=row['stredisko'],
                               fakulta=row['FakUniv'],
                               rozsah_vyucby=row['rozsah'],
                               konanie=row['konanie'],
                               cudzi_nazov=row['nazovJ'],
                               kredit=row['kredit'])
                    for row in app.d.zoznamPredmetovTable.loaded_rows]

        return (predmety, message)

    async def get_register_predmetov_fakulta_options(self) -> list[Option]:
        app = await self._open_register_predmetov()

        return app.d.fakultaUniverzitaComboBox.options

    async def get_register_predmetov_akademicky_rok_options(self) -> list[Option]:
        app = await self._open_register_predmetov()

        return app.d.akRokComboBox.options

    async def get_register_predmetov_semester_options(self) -> list[Option]:
        app = await self._open_register_predmetov()

        return app.d.semesterComboBox.options

    async def get_register_predmetov_stupen_options(self) -> list[Option]:
        app = await self._open_register_predmetov()

        return app.d.stupenPredmetuComboBox.options
