from aisikl.app import assert_ops
from fladgejt.helpers import CantOpenApplication, find_row, find_option, encode_key, decode_key
from fladgejt.structures import Predmet, Termin, PrihlasenyStudent
from fladgejt.webui.studium import WebuiStudiumMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from abc import ABC
    from aisikl.app import Application, Operation
    from aisikl.components.action import Action
    from aisikl.components.button import Button
    from aisikl.components.checkbox import CheckBox
    from aisikl.components.combobox import ComboBox
    from aisikl.components.table import Row, Table
    from aisikl.dialog import Dialog

    class TerminyHodnoteniaDialogsType(ABC, Dialog):
        aktualneTerminyCheckBox: CheckBox
        enterButton: Button
        filterAction: Action
        odstranitButton: Button
        predmetyTable: Table
        pridatButton: Button
        prihlaseniTable: Table
        semesterComboBox: ComboBox
        terminyTable: Table
        zobrazitTerminyAction: Action
        zobrazitTerminyComboBox: ComboBox
        zobrazitZoznamPrihlasenychAction: Action
        zoznamPrihlasenychStudentovAction: Action
        zoznamTerminovTable: Table
else:
    TerminyHodnoteniaDialogsType = None



class WebuiTerminyMixin(WebuiStudiumMixin):
    async def __vyber_oba_semestre(self, app: Application[TerminyHodnoteniaDialogsType]) -> None:
        index = find_option(app.d.semesterComboBox.options, title='')
        if app.d.semesterComboBox.selected_index != index:
            await app.d.semesterComboBox.select(index)
            await app.d.filterAction.execute()

    async def get_vidim_terminy_hodnotenia(self, zapisny_list_key: str) -> bool:
        try:
            await self._open_terminy_hodnotenia_app(zapisny_list_key)
        except CantOpenApplication:
            return False
        return True

    async def get_predmety(self, zapisny_list_key: str) -> list[Predmet]:
        app = await self._open_terminy_hodnotenia_app(zapisny_list_key)

        await self.__vyber_oba_semestre(app)

        result = [Predmet(skratka=row['skratka'],
                          nazov=row['nazov'],
                          typ_vyucby=row['kodTypVyucby'],
                          semester=row['semester'],
                          kredit=row['kredit'])
                  for row in await app.d.predmetyTable.all_rows()]
        return result

    async def get_prihlasene_terminy(self, zapisny_list_key: str) -> list[Termin]:
        app = await self._open_terminy_hodnotenia_app(zapisny_list_key)

        # V dolnom combo boxe dame "Zobrazit terminy: Vsetkych predmetov".
        await app.d.zobrazitTerminyComboBox.select(0)

        # Stlacime button vedla combo boxu.
        await app.d.zobrazitTerminyAction.execute()

        _studium_key, akademicky_rok = decode_key(zapisny_list_key)

        # Vytiahneme tabulku terminov.
        result = [Termin(datum=row['dat'],
                         cas=row['cas'],
                         miestnost=row['miestnosti'],
                         pocet_prihlasenych=row['pocetPrihlasenych'],
                         maximalne_prihlasenych=row['maxPocet'],
                         hodnotiaci=row['hodnotiaci'],
                         prihlasovanie=row['prihlasovanie'],
                         odhlasovanie=row['odhlasovanie'],
                         poznamka=row['poznamka'],
                         skratka_predmetu=row['predmetSkratka'],
                         nazov_predmetu=row['predmetNazov'],
                         hodnotenie_terminu=row['znamka'],
                         hodnotenie_predmetu=row['hodnPredmetu'],
                         moznost_prihlasit=row['moznostPrihlasenia'],
                         datum_prihlasenia=row['datumPrihlas'],
                         datum_odhlasenia=row['datumOdhlas'],
                         akademicky_rok=akademicky_rok,
                         zapisny_list_key=zapisny_list_key)
                  for row in await app.d.terminyTable.all_rows()
                  if not row['datumOdhlas']]
        return result

    async def get_vypisane_terminy(self, zapisny_list_key: str) -> list[Termin]:
        app = await self._open_terminy_hodnotenia_app(zapisny_list_key)

        await self.__vyber_oba_semestre(app)

        result: list[Termin] = []

        for row in await app.d.predmetyTable.all_rows():
            if row['pocetAktualnychTerminov'] == '0': continue
            result.extend(await self.get_vypisane_terminy_predmetu(
                zapisny_list_key, encode_key((row['skratka'],))))

        return result

    async def __open_vyber_terminu_dialog(self, app: Application[TerminyHodnoteniaDialogsType]) -> None:
        # Caller musi dialog potom zavriet, aby otvorena aplikacia bola zase
        # v konzistentnom stave pre dalsieho co ju pouzije.

        # Stlacime button "Prihlasit sa na termin" dole.
        with app.collect_operations() as ops:
            await app.d.pridatButton.click()

        # Otvori sa novy dialog.
        await app.awaited_open_dialog(ops)

    async def __select_predmet_row(self, app: Application[TerminyHodnoteniaDialogsType], predmet_key: str) -> Row:
        await self.__vyber_oba_semestre(app)

        (skratka,) = decode_key(predmet_key)
        index = find_row(await app.d.predmetyTable.all_rows(), skratka=skratka)
        await app.d.predmetyTable.select(index)

        return (await app.d.predmetyTable.all_rows())[index]

    async def get_vypisane_terminy_predmetu(self, zapisny_list_key: str, predmet_key: str) -> list[Termin]:
        app = await self._open_terminy_hodnotenia_app(zapisny_list_key)

        predmet_row = await self.__select_predmet_row(app, predmet_key)
        await self.__open_vyber_terminu_dialog(app)

        _studium_key, akademicky_rok = decode_key(zapisny_list_key)

        result = [Termin(datum=row['dat'],
                         cas=row['cas'],
                         miestnost=row['miestnosti'],
                         pocet_prihlasenych=row['pocetPrihlasenych'],
                         maximalne_prihlasenych=row['maxPocet'],
                         hodnotiaci=row['hodnotiaci'],
                         prihlasovanie=row['prihlasovanie'],
                         odhlasovanie=row['odhlasovanie'],
                         poznamka=row['poznamka'],
                         skratka_predmetu=predmet_row['skratka'],
                         nazov_predmetu=predmet_row['nazov'],
                         hodnotenie_terminu="",
                         hodnotenie_predmetu="",
                         moznost_prihlasit=row['moznostPrihlasenia'],
                         datum_prihlasenia="",
                         datum_odhlasenia="",
                         akademicky_rok=akademicky_rok,
                         zapisny_list_key=zapisny_list_key)
                  for row in await app.d.zoznamTerminovTable.all_rows()]

        # Stlacime zatvaraci button.
        with app.collect_operations() as ops:
            await app.d.click_close_button()

        # Dialog sa zavrie.
        await app.awaited_close_dialog(ops)

        return result

    async def get_prihlaseni_studenti(self, termin_key: str) -> list[PrihlasenyStudent]:
        zapisny_list_key, predmet_key, datum, cas, miestnost, poznamka = (
            decode_key(termin_key))

        app = await self._open_terminy_hodnotenia_app(zapisny_list_key)

        await self.__vyber_oba_semestre(app)
        await self.__select_predmet_row(app, predmet_key)

        await app.d.zobrazitTerminyAction.execute()
        try:
            index = find_row(
                await app.d.terminyTable.all_rows(),
                dat=datum, cas=cas, miestnosti=miestnost, poznamka=poznamka)
        except KeyError:
            index = None

        # Ak sa pozerame na stary zapisny list, vyber_terminov_dialog
        # bude disabled, preto termin musi byt v hlavnom dialogu.
        if index is not None:
            await app.d.terminyTable.select(index)
            # Stlacime "Zobrazit zoznam prihlasenych".
            with app.collect_operations() as ops:
                await app.d.zoznamPrihlasenychStudentovAction.execute()

            return await self.__process_prihlaseni_studenti_list(app, ops)
        else:
            # zapisny_list_key a predmet_key uz sme selectli predtym.
            return await self.__get_prihlaseni_studenti_cez_vyber_terminu(app,
                datum, cas, miestnost, poznamka)

    async def __get_prihlaseni_studenti_cez_vyber_terminu(self, app: Application[TerminyHodnoteniaDialogsType], datum: str, cas: str,
                                                    miestnost: str, poznamka: str) -> list[PrihlasenyStudent]:
        await self.__open_vyber_terminu_dialog(app)

        # Vyberieme spravny riadok. Ak v tabulke nie je, vypneme "Zobrazit len
        # aktualne terminy", stlacime nacitavaci button a skusime znovu.
        try:
            index = find_row(
                await app.d.zoznamTerminovTable.all_rows(),
                dat=datum, cas=cas, miestnosti=miestnost, poznamka=poznamka)
        except KeyError:
            index = None
        if index is None:
            await app.d.aktualneTerminyCheckBox.set_to(False)
            await app.d.zobrazitTerminyAction.execute()
            index = find_row(
                await app.d.zoznamTerminovTable.all_rows(),
                dat=datum, cas=cas, miestnosti=miestnost, poznamka=poznamka)
        await app.d.zoznamTerminovTable.select(index)

        # Stlacime "Zobrazit zoznam prihlasenych".
        with app.collect_operations() as ops:
            await app.d.zobrazitZoznamPrihlasenychAction.execute()

        result = await self.__process_prihlaseni_studenti_list(app, ops)

        # Stlacime zatvaraci button na zozname terminov.
        with app.collect_operations() as ops:
            await app.d.click_close_button()

        # Dialog sa zavrie.
        await app.awaited_close_dialog(ops)

        return result

    async def __process_prihlaseni_studenti_list(self, app: Application[TerminyHodnoteniaDialogsType], ops: list[Operation]) -> list[PrihlasenyStudent]:
        # Otvori sa zoznam prihlasenych.
        await app.awaited_open_dialog(ops)

        # Vytiahneme data z tabulky.
        result = [PrihlasenyStudent(sp_skratka=row['skratka'],
                                    datum_prihlasenia=row['datumPrihlas'],
                                    plne_meno=row['plneMeno'],
                                    rocnik=row['rocnik'],
                                    email=row['email'])
                  for row in await app.d.prihlaseniTable.all_rows()]

        # Stlacime zatvaraci button na zozname prihlasenych.
        with app.collect_operations() as ops:
            await app.d.click_close_button()

        # Dialog sa zavrie.
        await app.awaited_close_dialog(ops)

        return result

    async def prihlas_na_termin(self, termin_key: str) -> str | None:
        zapisny_list_key, predmet_key, datum, cas, miestnost, poznamka = (
            decode_key(termin_key))

        app = await self._open_terminy_hodnotenia_app(zapisny_list_key)
        await self.__select_predmet_row(app, predmet_key)
        await self.__open_vyber_terminu_dialog(app)

        # Vyberieme spravny riadok.
        await app.d.zoznamTerminovTable.select(find_row(
            await app.d.zoznamTerminovTable.all_rows(),
            dat=datum, cas=cas, miestnosti=miestnost, poznamka=poznamka))

        # Stlacime OK.
        with app.collect_operations() as ops:
            await app.d.enterButton.click()

        message = None
        if ops and ops[0].method == 'messageBox':
            assert_ops(ops, 'messageBox')
            message = ops[0].args[0]
            with app.collect_operations() as ops:
                await app.d.click_close_button()

        # Dialog sa zavrie.
        await app.awaited_close_dialog(ops)

        return message

    async def odhlas_z_terminu(self, termin_key: str) -> str | None:
        zapisny_list_key, predmet_key, datum, cas, miestnost, poznamka = (
            decode_key(termin_key))
        (skratka_predmetu,) = decode_key(predmet_key)

        app = await self._open_terminy_hodnotenia_app(zapisny_list_key)

        # V dolnom combo boxe dame "Zobrazit terminy: Vsetkych predmetov".
        await app.d.zobrazitTerminyComboBox.select(0)

        # Stlacime button vedla combo boxu.
        await app.d.zobrazitTerminyAction.execute()

        # Vyberieme spravny riadok.
        await app.d.terminyTable.select(find_row(
            await app.d.terminyTable.all_rows(),
            dat=datum, cas=cas, miestnosti=miestnost, poznamka=poznamka,
            predmetSkratka=skratka_predmetu))

        # Stlacime "Odhlasit sa z terminu".
        with app.collect_operations() as ops:
            await app.d.odstranitButton.click()

        # Vyskoci confirm box, ci sa naozaj chceme odhlasit. Stlacime "Ano".
        assert_ops(ops, 'confirmBox')
        with app.collect_operations() as ops:
            await app.confirm_box(2)

        if ops:
            assert_ops(ops, 'messageBox')
            return ops[0].args[0]

        return None
