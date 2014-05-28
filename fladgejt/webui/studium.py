
from aisikl.app import Application
from fladgejt.helpers import memoized, find_row
from fladgejt.structures import Studium, ZapisnyList, Hodnotenie


class WebuiStudiumMixin:
    @memoized
    def _open_administracia_studia(self):
        url = '/ais/servlets/WebUIServlet?appClassName=ais.gui.vs.es.VSES017App&kodAplikacie=VSES017&uiLang=SK'
        app, ops = Application.open(self.context, url)
        app.awaited_open_main_dialog(ops)
        return app

    def get_studia(self):
        app = self._open_administracia_studia()
        dlg = app.main_dialog

        result = [Studium(sp_skratka=row['studijnyProgramSkratka'],
                          sp_popis=row['studijnyProgramPopis'],
                          sp_doplnujuce_udaje=row['studijnyProgramDoplnUdaje'],
                          zaciatok=row['zaciatokStudia'],
                          koniec=row['koniecStudia'],
                          sp_dlzka=row['studijnyProgramDlzka'],
                          sp_cislo=row['studijnyProgramIdProgramCRS'],
                          rok_studia=row['rokStudia'])
                  for row in dlg.studiaTable.all_rows()]
        return result

    def get_zapisne_listy(self, studijny_program):
        app = self._open_administracia_studia()
        dlg = app.main_dialog

        self.__vyber_zapisny_list(dlg, studijny_program, None)
        result = [ZapisnyList(akademicky_rok=row['popisAkadRok'],
                              rocnik=row['rokRocnik'],
                              sp_skratka=row['studijnyProgramSkratka'],
                              sp_popis=row['studijnyProgramPopis'],
                              datum_zapisu=row['datumZapisu'])
                  for row in dlg.zapisneListyTable.all_rows()]

    def __vyber_zapisny_list(self, dlg, studijny_program, akademicky_rok):
        # Ak este nie je vybrate spravne studium, vyberieme ho a stlacime
        # nacitavaci button (sipku dole).
        studium_index = find_row(
            dlg.studiaTable.all_rows(),
            studijnyProgramSkratka=studijny_program)
        if dlg.studiaTable.selected_indexes != [studium_index] or len(dlg.zapisneListyTable.all_rows()) == 0:
            dlg.studiaTable.select(studium_index)
            dlg.nacitatButton.click()

        # Vyberieme zapisny list.
        if akademicky_rok is not None:
            zapisny_list_index = find_row(
                dlg.zapisneListyTable.all_rows(), popisAkadRok=akademicky_rok)
            dlg.zapisneListyTable.select(zapisny_list_index)

    @memoized
    def _open_terminy_hodnotenia_app(self, studijny_program, akademicky_rok):
        app = self._open_administracia_studia()
        dlg = app.main_dialog

        # Vyberieme spravne studium a zapisny list.
        self.__vyber_zapisny_list(dlg, studijny_program, akademicky_rok)

        # Stlacime v menu "Terminy hodnotenia".
        with app.collect_operations() as ops:
            dlg.terminyHodnoteniaAction.execute()

        # Otvori sa nove okno a v nom hlavny dialog.
        new_app, new_ops = app.awaited_start_app(ops)
        new_app.awaited_open_main_dialog(new_ops)
        return new_app

    @memoized
    def _open_hodnotenia_priemery_app(self, studijny_program, akademicky_rok):
        app = self._open_administracia_studia()
        dlg = app.main_dialog

        # Vyberieme spravne studium a zapisny list.
        self.__vyber_zapisny_list(dlg, studijny_program, akademicky_rok)

        # Stlacime v menu "Hodnotenia, priemery".
        with app.collect_operations() as ops:
            dlg.hodnoteniaPriemeryAction.execute()

        # Otvori sa nove okno a v nom hlavny dialog.
        new_app, new_ops = app.awaited_start_app(ops)
        new_app.awaited_open_main_dialog(new_ops)
        return new_app

    def get_prehlad_kreditov(self, studijny_program):
        app = self._open_administracia_studia()
        dlg = app.main_dialog

        # Vyberieme spravne studium.
        self.__vyber_zapisny_list(dlg, studijny_program, None)

        # Stlacime v menu "Kontrola" -> "Ziskanych kreditov, prehlad hodnotenia".
        with app.collect_operations() as ops:
            dlg.ziskaneMenuItem.click()

        # Otvori sa dialog s prehladom kreditov.
        dlg2 = app.awaited_open_dialog(ops)

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
                             hodn_znamka_popis=row['znamkaPopis'])
                  for row in dlg2.predmetyTable.all_rows()]

        # Stlacime zatvaraci button.
        with app.collect_operations() as ops:
            dlg2.click_close_button()

        # Dialog sa zavrie.
        app.awaited_close_dialog(dlg2)

        return result
