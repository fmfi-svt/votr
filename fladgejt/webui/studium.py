import re
from aisikl.app import Application, assert_ops, DEFAULT_IGNORED_MESSAGES
from aisikl.exceptions import AISBehaviorError
from fladgejt.base import BaseClient
from fladgejt.helpers import CantOpenApplication, find_row, find_option, encode_key, decode_key
from fladgejt.structures import Studium, ZapisnyList, Hodnotenie
from fladgejt.webui.pool import pooled_app
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from abc import ABC
    from aisikl.components.button import Button
    from aisikl.components.label import Label
    from aisikl.components.menuitem import MenuItem
    from aisikl.components.action import Action
    from aisikl.components.combobox import ComboBox, Option
    from aisikl.components.table import Table
    from aisikl.dialog import Dialog
    from fladgejt.webui.hodnotenia import HodnoteniaPriemeryDialogsType, PriebezneHodnotenieDialogsType
    from fladgejt.webui.terminy import TerminyHodnoteniaDialogsType
    from fladgejt.webui.zapis import ZapisPredmetovDialogsType

    class AdministraciaStudiaDialogsType(ABC, Dialog):
        studiaTable: Table
        zapisneListyTable: Table
        nacitatButton: Button
        kredityTable: Table
        pridatZapisnyListButton: Button
        terminyHodnoteniaAction: Action
        hodnoteniaPriemeryAction: Action
        ziskaneMenuItem: MenuItem
        predmetyTable: Table
        lop_statniceLabel: Label
        vsp_statniceLabel: Label
        rokComboBox: ComboBox
        closeButton: Button
        rocnikComboBox: ComboBox
        priebezneHodnotenieAction: Action
        zapisPredmetovKredityAction: Action
        enterButton: Button
        odobratZapisnyListButton: Button
else:
    AdministraciaStudiaDialogsType = None
    HodnoteniaPriemeryDialogsType = None
    PriebezneHodnotenieDialogsType = None
    TerminyHodnoteniaDialogsType = None
    ZapisPredmetovDialogsType = None


class GetPrehladKreditovResult(TypedDict):
    items: list[Hodnotenie]
    message: str | None
    kredity_ziskane: int | None
    kredity_zapisane: int | None
    priemer_ohodnotenych: str | None
    priemer_vsetkych: str | None


class WebuiStudiumMixin(BaseClient):
    @pooled_app
    def _open_administracia_studia(self) -> Application[AdministraciaStudiaDialogsType]:
        url = '/ais/servlets/WebUIServlet?fajr=A&appClassName=ais.gui.vs.es.VSES017App&kodAplikacie=VSES017&uiLang=SK'
        ignored_messages = DEFAULT_IGNORED_MESSAGES + ['Štúdium je prerušené. Zvoľte aktívne štúdium.']
        app, ops = Application[AdministraciaStudiaDialogsType].open(self.context, url, ignored_messages)
        app.awaited_open_main_dialog(ops)
        return app

    def get_som_student(self) -> bool:
        try:
            self._open_administracia_studia()
        except AISBehaviorError as e:
            if 'Neautorizovaný prístup!' in str(e):
                return False
            raise
        return True

    def get_studia(self) -> list[Studium]:
        app = self._open_administracia_studia()

        result = [Studium(sp_skratka=row['studijnyProgramSkratka'],
                          sp_popis=row['studijnyProgramPopis'],
                          sp_doplnujuce_udaje=row['studijnyProgramDoplnUdaje'],
                          zaciatok=row['zaciatokStudia'],
                          koniec=row['koniecStudia'],
                          sp_dlzka=row['studijnyProgramDlzka'],
                          sp_cislo=row['studijnyProgramIdProgramCRS'],
                          rok_studia=row['rokStudia'],
                          organizacna_jednotka=row['studijnyProgramSkratkaAkreditOJ'])
                  for row in app.d.studiaTable.all_rows()]
        return result

    def get_zapisne_listy(self, studium_key: str) -> list[ZapisnyList]:
        app = self._open_administracia_studia()

        self.__vyber_studium(app, studium_key)
        result = [ZapisnyList(akademicky_rok=row['popisAkadRok'],
                              rocnik=row['rokRocnik'],
                              sp_skratka=row['studProgramSkratka'],
                              sp_popis=row['studProgramPopis'],
                              datum_zapisu=row['datumZapisu'],
                              studium_key=studium_key)
                  for row in app.d.zapisneListyTable.all_rows()]
        return result

    def zapisny_list_key_to_akademicky_rok(self, zapisny_list_key: str) -> str:
        _studium_key, akademicky_rok = decode_key(zapisny_list_key)

        return akademicky_rok

    def __vyber_studium(self, app: Application[AdministraciaStudiaDialogsType], studium_key: str) -> None:
        sp_skratka, zaciatok = decode_key(studium_key)

        # Najdeme studium.
        studium_index = find_row(
            app.d.studiaTable.all_rows(),
            studijnyProgramSkratka=sp_skratka,
            zaciatokStudia=zaciatok)

        # Vyberieme studium a stlacime nacitavaci button (sipku dole).
        if app.d.studiaTable.selected_row_indexes != [studium_index] or len(app.d.zapisneListyTable.all_rows()) == 0:
            with app.collect_operations() as ops:
                app.d.studiaTable.select(studium_index)
            if ops:
                app.awaited_refresh_dialog(ops)

            with app.collect_operations() as ops:
                app.d.nacitatButton.click()

            if ops:
                app.awaited_refresh_dialog(ops)

    def __vyber_zapisny_list(self, app: Application[AdministraciaStudiaDialogsType], zapisny_list_key: str) -> None:
        studium_key, akademicky_rok = decode_key(zapisny_list_key)

        # Ak este nie je vybrate spravne studium, vyberieme ho.
        self.__vyber_studium(app, studium_key)

        # Vyberieme zapisny list.
        zapisny_list_index = find_row(
            app.d.zapisneListyTable.all_rows(), popisAkadRok=akademicky_rok)
        app.d.zapisneListyTable.select(zapisny_list_index)

    @pooled_app
    def _open_priebezne_hodnotenie_app(self, zapisny_list_key: str) -> Application[PriebezneHodnotenieDialogsType]:
        app = self._open_administracia_studia()

        # Vyberieme spravne studium a zapisny list.
        self.__vyber_zapisny_list(app, zapisny_list_key)

        # Stlacime v menu "Priebezne hodnotenie".
        with app.collect_operations() as ops:
            app.d.priebezneHodnotenieAction.execute()

        if not ops: raise CantOpenApplication()

        # Otvori sa nove okno a v nom hlavny dialog.
        new_app, new_ops = app.awaited_start_app(ops, hint=PriebezneHodnotenieDialogsType)
        new_app.awaited_open_main_dialog(new_ops)
        return new_app

    @pooled_app
    def _open_zapis_predmetov_app(self, zapisny_list_key: str) -> Application[ZapisPredmetovDialogsType]:
        app = self._open_administracia_studia()

        # Vyberieme spravne studium a zapisny list.
        self.__vyber_zapisny_list(app, zapisny_list_key)

        # Stlacime v menu "Zapis predmetov, kredity".
        with app.collect_operations() as ops:
            app.d.zapisPredmetovKredityAction.execute()

        if not ops: raise CantOpenApplication()

        # Otvori sa nove okno a v nom hlavny dialog.
        new_app, new_ops = app.awaited_start_app(ops, hint=ZapisPredmetovDialogsType)
        new_app.awaited_open_main_dialog(new_ops)
        return new_app

    @pooled_app
    def _open_terminy_hodnotenia_app(self, zapisny_list_key: str) -> Application[TerminyHodnoteniaDialogsType]:
        app = self._open_administracia_studia()

        # Vyberieme spravne studium a zapisny list.
        self.__vyber_zapisny_list(app, zapisny_list_key)

        # Stlacime v menu "Terminy hodnotenia".
        with app.collect_operations() as ops:
            app.d.terminyHodnoteniaAction.execute()

        if not ops: raise CantOpenApplication()

        # Otvori sa nove okno a v nom hlavny dialog.
        new_app, new_ops = app.awaited_start_app(ops, hint=TerminyHodnoteniaDialogsType)
        new_app.awaited_open_main_dialog(new_ops)
        return new_app

    @pooled_app
    def _open_hodnotenia_priemery_app(self, zapisny_list_key: str) -> Application[HodnoteniaPriemeryDialogsType]:
        app = self._open_administracia_studia()

        # Vyberieme spravne studium a zapisny list.
        self.__vyber_zapisny_list(app, zapisny_list_key)

        # Stlacime v menu "Hodnotenia, priemery".
        with app.collect_operations() as ops:
            app.d.hodnoteniaPriemeryAction.execute()

        if not ops: raise CantOpenApplication()

        # Otvori sa nove okno a v nom hlavny dialog.
        new_app, new_ops = app.awaited_start_app(ops, hint=HodnoteniaPriemeryDialogsType)
        new_app.awaited_open_main_dialog(new_ops)
        return new_app

    def get_prehlad_kreditov(self, studium_key: str) -> GetPrehladKreditovResult:
        app = self._open_administracia_studia()

        # Vyberieme spravne studium.
        self.__vyber_studium(app, studium_key)

        # Stlacime v menu "Kontrola" -> "Ziskanych kreditov, prehlad hodnotenia".
        with app.collect_operations() as ops:
            app.d.ziskaneMenuItem.click()

        if not ops:
            return GetPrehladKreditovResult(
                items=[],
                message="Prehľad hodnotenia pre toto štúdium nie je dostupný.",
                kredity_ziskane=None,
                kredity_zapisane=None,
                priemer_ohodnotenych=None,
                priemer_vsetkych=None,
            )

        # Otvori sa dialog s prehladom kreditov.
        app.awaited_open_dialog(ops)

        # Vytiahneme tabulku predmetov.
        result = [Hodnotenie(akademicky_rok=row['akRok'],
                             skratka=row['skratka'],
                             nazov=row['nazov'],
                             typ_vyucby=row['kodTypVyucbySP'],
                             semester=row['semester'],
                             kredit=row['kredit'],
                             hodn_znamka=row['znamka'],
                             hodn_termin=row['termin'],
                             hodn_datum=row['datum'],
                             hodn_znamka_popis=row['znamkaPopis'],
                             nahradeny=(row['nahradzaMa'] != ''),
                             poplatok=row['poplatok'],
                             zapisny_list_key=encode_key(
                                (studium_key, row['akRok'])))
                  for row in app.d.predmetyTable.all_rows()]

        kredity_ziskane, kredity_zapisane = self.__get_sucty_kreditov(app)

        # "Vážený študijný priemer aj s časťou štátne skúšky:" / "Len ohodnotených predmetov:"
        # tool_tip_text ma viac cifier presnosti.
        priemer_ohodnotenych = app.d.lop_statniceLabel.tool_tip_text
        # "Vážený študijný priemer aj s časťou štátne skúšky:"
        priemer_vsetkych = app.d.vsp_statniceLabel.tool_tip_text

        # Stlacime zatvaraci button.
        with app.collect_operations() as ops:
            app.d.click_close_button()

        # Dialog sa zavrie.
        app.awaited_close_dialog(ops)

        return GetPrehladKreditovResult(
            items=result,
            message=None,
            kredity_ziskane=kredity_ziskane,
            kredity_zapisane=kredity_zapisane,
            priemer_ohodnotenych=priemer_ohodnotenych,
            priemer_vsetkych=priemer_vsetkych,
        )

    def __get_sucty_kreditov(self, app: Application[AdministraciaStudiaDialogsType]) -> tuple[int | None, int | None]:
        # Najdeme v tabulke suctov kreditov posledny riadok. V prvom stlpci ("Popis") by malo byt "SPOLU".
        rows = app.d.kredityTable.all_rows()
        if not rows:
            self.context.log('warning', 'kredityTable is empty')
            return None, None

        last = rows[-1]
        if last['popis'] != 'SPOLU':
            self.context.log('warning', 'kredityTable popis is wrong', last)
            return None, None

        # V poslednom stlpci "Spolu  (Zapísané/Získané + Uznané + Dovezené)" by mali byt dve cele cisla.
        if not (m := re.fullmatch(r'(\d+) / (\d+)', last['spolus'])):
            self.context.log('warning', 'kredityTable spolus is unexpected', last)
            return None, None

        return int(m.group(2)), int(m.group(1))

    def __open_novy_zapisny_list_dialog(self, app: Application[AdministraciaStudiaDialogsType], studium_key: str) -> None:
        # Vyberieme studium.
        self.__vyber_studium(app, studium_key)

        # Klikneme na tlacidlo pridania noveho zapisneho listu.
        with app.collect_operations() as ops:
            app.d.pridatZapisnyListButton.click()
        app.awaited_open_dialog(ops)

    def get_akademicke_roky_noveho_zapisneho_listu(self, studium_key: str) -> list[Option]:
        '''Gets available values for the academic year option when creating a
        new enrollment list.

        Args:
            studium_key: studium identifier

        Returns:
            A list of :class: `~Option` objects.
        '''
        app = self._open_administracia_studia()

        self.__open_novy_zapisny_list_dialog(app, studium_key)
        options = app.d.rokComboBox.options

        with app.collect_operations() as ops:
            app.d.closeButton.click()
        app.awaited_close_dialog(ops)

        return options

    def get_roky_studia_noveho_zapisneho_listu(self, studium_key: str) -> list[Option]:
        '''Gets available values for the study year option when creating a
        new enrollment list.

        Args:
            studium_key: studium identifier

        Returns:
            A list of :class: `~Option` objects.
        '''
        app = self._open_administracia_studia()

        self.__open_novy_zapisny_list_dialog(app, studium_key)
        options = app.d.rocnikComboBox.options

        with app.collect_operations() as ops:
            app.d.closeButton.click()
        app.awaited_close_dialog(ops)

        return options

    def create_zapisny_list(self, studium_key: str, akademicky_rok: str | None, rok_studia: str | None) -> str | None:
        '''Creates enrollment list.

        Args:
            studium_key: studium identifier
            akademicky_rok: Academic year of the time range in the form of
                'start/end'. E.g. '2013/2014'. (optional)
            rok_studia: year of the study
        '''
        app = self._open_administracia_studia()

        self.__open_novy_zapisny_list_dialog(app, studium_key)

        message = None

        # V combo boxe vyberieme rok studia.
        if rok_studia is not None:
            app.d.rocnikComboBox.select(find_option(app.d.rocnikComboBox.options, id=str(rok_studia)))

        # Ak je nastaveny akademicky rok, vyberieme ho v combo boxe.
        if akademicky_rok is not None:
            try:
                option = find_option(app.d.rokComboBox.options, id=akademicky_rok)
            # Snazime sa vytvorit zapisny list na akademicky rok, ktory nie je na vyber v comboBoxe
            except KeyError:
                with app.collect_operations() as ops:
                    app.d.click_close_button()
                app.awaited_close_dialog(ops)
                return "Na tento akademický rok sa nedá vytvoriť zápisný list."

            app.d.rokComboBox.select(option)

        # Stlacime tlacidlo "OK".
        with app.collect_operations() as ops:
            app.d.enterButton.click()

        # Ak sa neda vytvorit zapisny list, lebo to nie je povolene v danom datume
        if ops and ops[0].method == 'messageBox':
            assert_ops(ops, 'messageBox')
            message = ops[0].args[0]
            with app.collect_operations() as ops:
                app.d.click_close_button()

        # Dialog sa zavrie.
        app.awaited_close_dialog(ops)

        return message

    # nepouzita funkcia
    def delete_zapisny_list(self, zapisny_list_key: str) -> None:
        '''Deletes enrollment list.

        Args:
            zapisny_list_key: enrollment list identifier
        '''
        app = self._open_administracia_studia()

        # Vyberieme zapisny list.
        self.__vyber_zapisny_list(app, zapisny_list_key)

        # Klikneme na tlacidlo zrusenia zapisneho listu.
        with app.collect_operations() as ops:
            app.d.odobratZapisnyListButton.click()

        # Vyskoci confirm box, ci naozaj chceme odstranit zapisny list. Stlacime "Ano".
        assert_ops(ops, 'confirmBox')
        with app.collect_operations() as ops:
            app.confirm_box(2)
