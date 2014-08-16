
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

        result = [Studium(sp_skratka=row['studijnyProgramSkratka'],
                          sp_popis=row['studijnyProgramPopis'],
                          sp_doplnujuce_udaje=row['studijnyProgramDoplnUdaje'],
                          zaciatok=row['zaciatokStudia'],
                          koniec=row['koniecStudia'],
                          sp_dlzka=row['studijnyProgramDlzka'],
                          sp_cislo=row['studijnyProgramIdProgramCRS'],
                          rok_studia=row['rokStudia'])
                  for row in app.d.studiaTable.all_rows()]
        return result

    def get_zapisne_listy(self, studijny_program):
        app = self._open_administracia_studia()

        self.__vyber_zapisny_list(app, studijny_program, None)
        result = [ZapisnyList(akademicky_rok=row['popisAkadRok'],
                              rocnik=row['rokRocnik'],
                              sp_skratka=row['studProgramSkratka'],
                              sp_popis=row['studProgramPopis'],
                              datum_zapisu=row['datumZapisu'])
                  for row in app.d.zapisneListyTable.all_rows()]
        return result

    def __vyber_zapisny_list(self, app, studijny_program, akademicky_rok):
        # Ak este nie je vybrate spravne studium, vyberieme ho a stlacime
        # nacitavaci button (sipku dole).
        studium_index = find_row(
            app.d.studiaTable.all_rows(),
            studijnyProgramSkratka=studijny_program)
        if app.d.studiaTable.selected_row_indexes != [studium_index] or len(app.d.zapisneListyTable.all_rows()) == 0:
            app.d.studiaTable.select(studium_index)
            app.d.nacitatButton.click()

        # Vyberieme zapisny list.
        if akademicky_rok is not None:
            zapisny_list_index = find_row(
                app.d.zapisneListyTable.all_rows(), popisAkadRok=akademicky_rok)
            app.d.zapisneListyTable.select(zapisny_list_index)

    @memoized
    def _open_terminy_hodnotenia_app(self, studijny_program, akademicky_rok):
        app = self._open_administracia_studia()

        # Vyberieme spravne studium a zapisny list.
        self.__vyber_zapisny_list(app, studijny_program, akademicky_rok)

        # Stlacime v menu "Terminy hodnotenia".
        with app.collect_operations() as ops:
            app.d.terminyHodnoteniaAction.execute()

        # Otvori sa nove okno a v nom hlavny dialog.
        new_app, new_ops = app.awaited_start_app(ops)
        new_app.awaited_open_main_dialog(new_ops)
        return new_app

    @memoized
    def _open_hodnotenia_priemery_app(self, studijny_program, akademicky_rok):
        app = self._open_administracia_studia()

        # Vyberieme spravne studium a zapisny list.
        self.__vyber_zapisny_list(app, studijny_program, akademicky_rok)

        # Stlacime v menu "Hodnotenia, priemery".
        with app.collect_operations() as ops:
            app.d.hodnoteniaPriemeryAction.execute()

        # Otvori sa nove okno a v nom hlavny dialog.
        new_app, new_ops = app.awaited_start_app(ops)
        new_app.awaited_open_main_dialog(new_ops)
        return new_app

    def get_prehlad_kreditov(self, studijny_program):
        app = self._open_administracia_studia()

        # Vyberieme spravne studium.
        self.__vyber_zapisny_list(app, studijny_program, None)

        # Stlacime v menu "Kontrola" -> "Ziskanych kreditov, prehlad hodnotenia".
        with app.collect_operations() as ops:
            app.d.ziskaneMenuItem.click()

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
                             hodn_znamka_popis=row['znamkaPopis'])
                  for row in app.d.predmetyTable.all_rows()]

        # Stlacime zatvaraci button.
        with app.collect_operations() as ops:
            app.d.click_close_button()

        # Dialog sa zavrie.
        app.awaited_close_dialog(ops)

        return result
