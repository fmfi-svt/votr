from aisikl.components.button import Button
from aisikl.operations import CloseDialogOp, ConfirmBoxOp, MessageBoxOp, OpenDialogOp
from aisikl.typeutils import ct, nn
from fladgejt.base import BaseClient
from fladgejt.helpers import CantOpenApplication, find_row, find_option, decode_key
from fladgejt.structures import ZapisPredmet, ZapisVlastnost
from fladgejt.webui.commonui import select_text_ciselnik, show_all_columns
from fladgejt.webui.studium import WebuiStudiumMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from abc import ABC
    from aisikl.app import Application
    from aisikl.components.action import Action
    from aisikl.components.combobox import ComboBox, Option
    from aisikl.components.table import Table
    from aisikl.components.textfield import TextField
    from aisikl.components.tree import Tree
    from aisikl.dialog import Dialog

    class ZapisPredmetovDialogsType(ABC, Dialog):
        castiZapisnehoListuTree: Tree
        enterButton: Button
        fakultaComboBox: ComboBox
        odobratPredmetButton: Button
        predmetNazovTextField: TextField
        predmetSkratkaTextField: TextField
        predmetyTable: Table
        pridatPredmetAction: Action
        pridatPredmetZPonukyAction: Action
        rocnikComboBox: ComboBox
        strediskoSkratkaTextField: TextField
        strediskoTextTextField: TextField
        typComboBox: ComboBox
        vlastnostiStudProgramuTable: Table
        vybratStrediskoAction: Action
        zmazatStrediskoAction: Action
        zobrazitPredmetyAction: Action
        zobrazitPredmetyButton: Button
else:
    ZapisPredmetovDialogsType = None


UNAVAILABLE = "Zápis predmetov pre tento zápisný list nie je dostupný."


class WebuiZapisMixin(WebuiStudiumMixin, BaseClient):
    async def zapis_get_zapisane_predmety(self, zapisny_list_key: str, cast: str) -> tuple[list[ZapisPredmet], str | None]:
        try:
            app = await self._open_zapis_predmetov_app(zapisny_list_key)
        except CantOpenApplication:
            return ([], UNAVAILABLE)
        await self.__zatvor_ponuku_predmetov(app)

        # Oznacime vrchol pre celu cast, aby sme videli vsetky predmety.
        await app.d.castiZapisnehoListuTree.select('nR/' + cast)

        result = [ZapisPredmet(skratka=row['skratka'],
                               nazov=row['nazov'],
                               typ_vyucby=row['kodTypVyucby'],
                               semester=row['semester'],
                               kredit=row['kredit'],
                               rozsah_vyucby=row['rozsah'],
                               jazyk=row['jazyk'],
                               datum_zapisu=row['datumZapisu'],
                               aktualnost=row['aktualnost'],
                               pocet_prihlasenych=None,
                               maximalne_prihlasenych=None,
                               blok_skratka=row['skratkaBlok'],
                               blok_nazov=row['popisBlok'],
                               blok_index=None,
                               v_bloku_index=None,
                               odporucany_rocnik=None,
                               cast=row['kodCastStPlanu'])
                  for row in await app.d.predmetyTable.all_rows()]
        return (result, None)

    async def zapis_get_vlastnosti_programu(self, zapisny_list_key: str) -> tuple[list[ZapisVlastnost], str | None]:
        try:
            app = await self._open_zapis_predmetov_app(zapisny_list_key)
        except CantOpenApplication:
            return ([], UNAVAILABLE)
        await self.__zatvor_ponuku_predmetov(app)

        result = [ZapisVlastnost(skratka=row['skratka'],
                                 nazov=row['nazov'],
                                 minimalny_kredit=row['kredit'],
                                 poznamka=row['poznamky'])
                  for row in await app.d.vlastnostiStudProgramuTable.all_rows()]
        return (result, None)

    async def zapis_plan_vyhladaj(self, zapisny_list_key: str, cast: str) -> tuple[list[ZapisPredmet], str | None]:
        try:
            app = await self._open_zapis_predmetov_app(zapisny_list_key)
        except CantOpenApplication:
            return ([], UNAVAILABLE)
        await self.__zatvor_ponuku_predmetov(app)

        # AIS ponuka styri dialogy na pridavanie predmetov:
        # (1) "Pridat predmet zo studijneho planu"
        # (2) "Pridat predmet z ponuky predmetov"
        # (3) "Pridat neabsolvovany predmet"
        # (4) "Pridat odporucany predmet"
        # Zoznam ponukanych predmetov sa da zistit cez (1), (2) aj (4). (Pre
        # (2) mozme dat vyhladat vsetky predmety a zoradit ich podla bloku. Ale
        # to je dost pomale.) My pouzivame (1), lebo v tabulke su viacere dobre
        # stlpce, ako odporucany rocnik a "oficialne poradie" predmetov. Lenze
        # tieto stlpce su schovane, takze ich najprv musime zobrazit.

        # Optimalizacia pre SC (Studijna cast): Staci otvorit iba C (Vyberove
        # predmety), mozme vypnut filtrovanie podla typu vyucby a uvidime aj
        # A a B. Ale nesmieme ich tak zapisovat, lebo AIS ich zapise ako C, co
        # na studijnom nemaju radi.

        result: list[ZapisPredmet] = []

        # Skusime kazdy vrchol stromu, co nas zaujima.
        for id, node in app.d.castiZapisnehoListuTree.nodes.items():
            if not node.is_leaf: continue
            if '/' + cast + '/' not in id: continue
            if id in ('nR/SC/A', 'nR/SC/B'): continue

            # Oznacime dany vrchol stromu.
            await app.d.castiZapisnehoListuTree.select(id)

            # Stlacime "Pridat predmet zo studijneho planu".
            ops = await app.d.pridatPredmetAction.execute(return_ops=True)

            # Mozno vyskoci chyba.
            if ops.has_types(MessageBoxOp):
                return ([], ops.expect_one(MessageBoxOp).message)

            # Otvori sa novy dialog.
            await ops.expect_one(OpenDialogOp).perform()

            # Zapneme schovane stlpce.
            want = ['kodTypVyucby', 'popis', 'poradieB', 'poradieP', 'kodCastSP']
            if any(col not in app.d.predmetyTable.column_map for col in want):
                await show_all_columns(app, app.d.predmetyTable)

            # Zrusime filter podla odporucaneho rocniku.
            index = find_option(app.d.rocnikComboBox.options, title='')
            await app.d.rocnikComboBox.select(index)

            # Ak sa da, zrusime filter podla typu vyucby.
            if app.d.typComboBox.is_really_enabled():
                index = find_option(app.d.typComboBox.options, title='')
                await app.d.typComboBox.select(index)

            # Nacitame vsetky predmety.
            await app.d.zobrazitPredmetyButton.click()

            result.extend(ZapisPredmet(skratka=row['skratkaPredmet'],
                                       nazov=row['nazovPredmet'],
                                       typ_vyucby=row['kodTypVyucby'],
                                       semester=row['kodSemester'],
                                       kredit=row['kredit'],
                                       rozsah_vyucby=row['rozsah'],
                                       jazyk=row['jazyk'],
                                       datum_zapisu=None,
                                       aktualnost=row['kodAktualnost'],
                                       pocet_prihlasenych=row['pocetStudentov'],
                                       maximalne_prihlasenych=row['obmedzenie'],
                                       blok_skratka=row['skratkaBlok'],
                                       blok_nazov=row['popis'],
                                       blok_index=row['poradieB'],
                                       v_bloku_index=row['poradieP'],
                                       odporucany_rocnik=row['rocnik'],
                                       cast=row['kodCastSP'])
                          for row in await app.d.predmetyTable.all_rows())

            # Ked sme hotovi, zavrieme dialog.
            ops = await app.d.click_close_button(return_ops=True)
            await ops.expect_one(CloseDialogOp).perform()

        return (result, None)

    async def zapis_plan_pridaj_predmety(self, zapisny_list_key: str, cast: str,
                                   dvojice_typ_vyucby_skratka: list[tuple[str, str]]) -> str | None:
        try:
            app = await self._open_zapis_predmetov_app(zapisny_list_key)
        except CantOpenApplication:
            return UNAVAILABLE
        await self.__zatvor_ponuku_predmetov(app)

        # Zistime, ake vsetky typy vyucby chceme zapisat.
        typy_vyucby = sorted(set(
            typ_vyucby for typ_vyucby, _skratka in dvojice_typ_vyucby_skratka))

        for typ_vyucby in typy_vyucby:
            # Oznacime dany vrchol stromu.
            id = 'nR/' + cast + '/' + typ_vyucby
            await app.d.castiZapisnehoListuTree.select(id)

            # Stlacime "Pridat predmet zo studijneho planu".
            ops = await app.d.pridatPredmetAction.execute(return_ops=True)

            # Mozno vyskoci chyba.
            if ops.has_types(MessageBoxOp):
                return ops.expect_one(MessageBoxOp).message

            # Otvori sa novy dialog.
            await ops.expect_one(OpenDialogOp).perform()

            # Skusime, ci uz teraz vidime vsetky hladane predmety.
            found_all = True
            for typ_vyucby_predmetu, skratka in dvojice_typ_vyucby_skratka:
                if typ_vyucby != typ_vyucby_predmetu: continue
                try:
                    find_row(
                        await app.d.predmetyTable.all_rows(), skratkaPredmet=skratka)
                except KeyError:
                    found_all = False

            if not found_all:
                # Ak nevidime, zrusime filter podla odporucaneho rocniku.
                index = find_option(app.d.rocnikComboBox.options, title='')
                await app.d.rocnikComboBox.select(index)

                # Nacitame vsetky predmety.
                await app.d.zobrazitPredmetyButton.click()

            # Teraz uz by sme mali vidiet vsetky predmety, co chceme zapisat.
            # Postupne ich najdeme a zapneme checkboxy.
            for typ_vyucby_predmetu, skratka in dvojice_typ_vyucby_skratka:
                if typ_vyucby != typ_vyucby_predmetu: continue
                index = find_row(
                    await app.d.predmetyTable.all_rows(), skratkaPredmet=skratka)
                await app.d.predmetyTable.edit_cell('p', index, True)

            # Stlacime "OK".
            ops = await app.d.enterButton.click(return_ops=True)

            # Mozno vyskoci confirm box. (Napriklad nas upozornuje, ze niektore
            # predmety uz mame zapisane. O inych confirm boxoch nevieme, a
            # dufame, ze su neskodne.) Zvolime "Ano".
            if ops.has_types(ConfirmBoxOp):
                ops = await ops.expect_one(ConfirmBoxOp).reply(
                    ConfirmBoxOp.Option.YES, return_ops=True)

            # Mozno vyskoci chyba.
            message = None
            if ops.has_types(MessageBoxOp):
                message = ops.expect_one(MessageBoxOp).message
                ops = await app.d.click_close_button(return_ops=True)

            # Dialog sa zavrie.
            await ops.expect_one(CloseDialogOp).perform()

            if message: return message

        return None

    async def __zatvor_ponuku_predmetov(self, app: Application[ZapisPredmetovDialogsType]) -> None:
        if app.d.name == 'VSES260_PridaniePredmetuDlg1':
            ops = await app.d.click_close_button(return_ops=True)
            await ops.expect_one(CloseDialogOp).perform()

    async def __otvor_ponuku_predmetov(self, app: Application[ZapisPredmetovDialogsType]) -> str | None:
        if app.d.name != 'VSES260_PridaniePredmetuDlg1':
            # Oznacime vrchol SC - C. (V ponuke predmetov nezalezi, aky typ
            # vyucby zvolime, a zapise sa spravne.)
            await app.d.castiZapisnehoListuTree.select('nR/SC/C')

            # Stlacime "Pridat predmet z ponuky predmetov".
            ops = await app.d.pridatPredmetZPonukyAction.execute(return_ops=True)

            # Mozno vyskoci chyba.
            if ops.has_types(MessageBoxOp):
                return ops.expect_one(MessageBoxOp).message

            # Otvori sa novy dialog.
            await ops.expect_one(OpenDialogOp).perform()

    async def __query_ponuka_predmetov(self, app: Application[ZapisPredmetovDialogsType], fakulta: str | None, stredisko: str | None,
                                 filter_skratka: str | None, filter_nazov: str | None) -> str | None:
        message = await self.__otvor_ponuku_predmetov(app)
        if message:
            return message

        if (nn(app.d.fakultaComboBox.selected_option).id == (fakulta or '') and
            app.d.predmetSkratkaTextField.value == (filter_skratka or '') and
            app.d.predmetNazovTextField.value == (filter_nazov or '') and
            app.d.strediskoSkratkaTextField.value == (stredisko or '') and
            (not stredisko or not app.d.strediskoTextTextField.value)):
            return None

        await app.d.fakultaComboBox.select(find_option(app.d.fakultaComboBox.options, id=(fakulta or '')))

        await app.d.predmetSkratkaTextField.write(filter_skratka or '')

        await app.d.predmetNazovTextField.write(filter_nazov or '')

        if not await select_text_ciselnik(
            app, stredisko, app.d.strediskoSkratkaTextField,
            # vola sa "c1Button", ale fuj, to tu nechcem hardcodovat
            ct(Button, app.d.zmazatStrediskoAction.get_components()[0]),
            # vola sa "Button", ale fuj, to tu nechcem hardcodovat
            ct(Button, app.d.vybratStrediskoAction.get_components()[0]),
            'skratka',
        ):
            return "Stredisko neexistuje."

        await app.d.zobrazitPredmetyAction.execute()

        while not app.d.predmetyTable.is_end_of_data:
            await app.d.predmetyTable.scroll_down(10)

        return None

    async def zapis_ponuka_vyhladaj(self, zapisny_list_key: str, fakulta: str | None, stredisko: str | None,
                              filter_skratka: str | None, filter_nazov: str | None) -> tuple[list[ZapisPredmet], str | None]:
        try:
            app = await self._open_zapis_predmetov_app(zapisny_list_key)
        except CantOpenApplication:
            return ([], UNAVAILABLE)

        # Otvorime ponuku predmetov a vyhladame predmety.
        message = await self.__query_ponuka_predmetov(
            app, fakulta, stredisko, filter_skratka, filter_nazov)
        if message:
            return ([], message)

        if app.d.predmetyTable.truncated:
            message = "Neboli načítané všetky dáta. Upresnite kritériá vyhľadávania."

        result = [ZapisPredmet(skratka=row['skratkaPredmet'],
                               nazov=row['nazovPredmet'],
                               typ_vyucby=row['kodTypVyucby'],
                               semester=row['kodSemester'],
                               kredit=row['kredit'],
                               rozsah_vyucby=row['rozsah'],
                               jazyk=row['jazyk'],
                               datum_zapisu=None,
                               aktualnost=row['kodAktualnost'],
                               pocet_prihlasenych=row['pocetStudentov'],
                               maximalne_prihlasenych=row['obmedzenie'],
                               blok_skratka=row['skratkaBlok2'],
                               blok_nazov=None,
                               blok_index=None,
                               v_bloku_index=None,
                               odporucany_rocnik=None,
                               cast='SC')
                  for row in app.d.predmetyTable.loaded_rows]
        return (result, message)

    async def zapis_ponuka_pridaj_predmety(self, zapisny_list_key: str, fakulta: str | None, stredisko: str | None,
                                     filter_skratka: str | None, filter_nazov: str | None,
                                     zvolene_skratky: list[str]) -> str | None:
        try:
            app = await self._open_zapis_predmetov_app(zapisny_list_key)
        except CantOpenApplication:
            return UNAVAILABLE

        # Otvorime ponuku predmetov a vyhladame predmety.
        message = await self.__query_ponuka_predmetov(
            app, fakulta, stredisko, filter_skratka, filter_nazov)
        if message:
            return message

        # Odznacime vsetky vyznacene predmety (nemalo by sa stat).
        for row in app.d.predmetyTable.loaded_rows:
            if row.cell('p').value == True:
                await app.d.predmetyTable.edit_cell('p', row.id, False)

        # Vyznacime predmety, co si chceme zapisat.
        for skratka in zvolene_skratky:
            index = find_row(
                app.d.predmetyTable.loaded_rows, skratkaPredmet=skratka)
            await app.d.predmetyTable.edit_cell('p', index, True)

        # Stlacime "OK".
        ops = await app.d.enterButton.click(return_ops=True)

        # Mozno vyskoci confirm box. (Napriklad nas upozornuje, ze niektore
        # predmety uz mame zapisane. O inych confirm boxoch nevieme, a
        # dufame, ze su neskodne.) Zvolime "Ano".
        if ops.has_types(ConfirmBoxOp):
            ops = await ops.expect_one(ConfirmBoxOp).reply(
                ConfirmBoxOp.Option.YES, return_ops=True)

        # Mozno vyskoci chyba. (Dialog zostane otvoreny.)
        if ops.has_types(MessageBoxOp):
            return ops.expect_one(MessageBoxOp).message

        # Dialog sa zavrie.
        await ops.expect_one(CloseDialogOp).perform()

        return None

    async def zapis_ponuka_options(self, zapisny_list_key: str) -> tuple[list[Option], str | None]:
        try:
            app = await self._open_zapis_predmetov_app(zapisny_list_key)
        except CantOpenApplication:
            return ([], UNAVAILABLE)

        message = await self.__otvor_ponuku_predmetov(app)
        if message:
            return ([], message)

        return (app.d.fakultaComboBox.options, None)

    async def zapis_odstran_predmety(self, zapisny_list_key: str, cast: str, predmet_key_list: list[str]) -> str | None:
        try:
            app = await self._open_zapis_predmetov_app(zapisny_list_key)
        except CantOpenApplication:
            return UNAVAILABLE
        await self.__zatvor_ponuku_predmetov(app)

        # Oznacime vrchol pre celu cast, aby sme videli vsetky predmety.
        await app.d.castiZapisnehoListuTree.select('nR/' + cast)

        # Vyberieme v tabulke dane predmety.
        indexes: list[int] = []
        for predmet_key in predmet_key_list:
            (skratka_predmetu,) = decode_key(predmet_key)
            indexes.append(find_row(
                await app.d.predmetyTable.all_rows(),
                skratka=skratka_predmetu))
        await app.d.predmetyTable.select(indexes)

        # Stlacime "Odobrat predmet".
        ops = await app.d.odobratPredmetButton.click(return_ops=True)

        # Mozno vyskoci confirm box. Zvolime "Ano".
        if ops.has_types(ConfirmBoxOp):
            ops = await ops.expect_one(ConfirmBoxOp).reply(
                ConfirmBoxOp.Option.YES, return_ops=True)

        # Mozno vyskoci chyba. Ak nie, sme hotovi.
        if ops:
            return ops.expect_one(MessageBoxOp).message

        return None
