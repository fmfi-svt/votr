# -*- coding: utf-8 -*-

from aisikl.app import Application, assert_ops
from aisikl.exceptions import AISBehaviorError
from fladgejt.helpers import find_row, find_option, with_key_args
from fladgejt.structures import Studium, ZapisnyList, Hodnotenie
from fladgejt.webui.pool import pooled_app


class WebuiStudiumMixin:
    @pooled_app
    def _open_administracia_studia(self):
        url = '/ais/servlets/WebUIServlet?fajr=A&appClassName=ais.gui.vs.es.VSES017App&kodAplikacie=VSES017&uiLang=SK'
        app, ops = Application.open(self.context, url)
        app.awaited_open_main_dialog(ops)
        return app

    def get_som_student(self):
        try:
            self._open_administracia_studia()
        except AISBehaviorError as e:
            if 'Neautorizovaný prístup!' in str(e):
                return False
            raise
        return True

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

    @with_key_args(True)
    def get_zapisne_listy(self, studium_key):
        app = self._open_administracia_studia()

        self.__vyber_studium(app, studium_key)
        result = [ZapisnyList(akademicky_rok=row['popisAkadRok'],
                              rocnik=row['rokRocnik'],
                              sp_skratka=row['studProgramSkratka'],
                              sp_popis=row['studProgramPopis'],
                              datum_zapisu=row['datumZapisu'])
                  for row in app.d.zapisneListyTable.all_rows()]
        return result

    def __vyber_studium(self, app, studium_key):
        sp_skratka, zaciatok = studium_key

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

    def __vyber_zapisny_list(self, app, studium_key, zapisny_list_key):
        # Ak este nie je vybrate spravne studium, vyberieme ho.
        self.__vyber_studium(app, studium_key)

        # Vyberieme zapisny list.
        (akademicky_rok,) = zapisny_list_key
        zapisny_list_index = find_row(
            app.d.zapisneListyTable.all_rows(), popisAkadRok=akademicky_rok)
        app.d.zapisneListyTable.select(zapisny_list_index)

    @pooled_app
    def _open_terminy_hodnotenia_app(self, studium_key, zapisny_list_key):
        app = self._open_administracia_studia()

        # Vyberieme spravne studium a zapisny list.
        self.__vyber_zapisny_list(app, studium_key, zapisny_list_key)

        # Stlacime v menu "Terminy hodnotenia".
        with app.collect_operations() as ops:
            app.d.terminyHodnoteniaAction.execute()

        # Otvori sa nove okno a v nom hlavny dialog.
        new_app, new_ops = app.awaited_start_app(ops)
        new_app.awaited_open_main_dialog(new_ops)
        return new_app

    def get_hodnotenia_priemery_app(self, studium_key, zapisny_list_key):
        app = self._open_administracia_studia()

        if not app.d.hodnoteniaPriemeryAction.accessible:
            return None

        return self._open_hodnotenia_priemery_app(studium_key, zapisny_list_key)

    @pooled_app
    def _open_hodnotenia_priemery_app(self, studium_key, zapisny_list_key):
        app = self._open_administracia_studia()

        # Vyberieme spravne studium a zapisny list.
        self.__vyber_zapisny_list(app, studium_key, zapisny_list_key)

        # Stlacime v menu "Hodnotenia, priemery".
        with app.collect_operations() as ops:
            app.d.hodnoteniaPriemeryAction.execute()

        # Otvori sa nove okno a v nom hlavny dialog.
        new_app, new_ops = app.awaited_start_app(ops)
        new_app.awaited_open_main_dialog(new_ops)
        return new_app

    @with_key_args(True)
    def get_prehlad_kreditov(self, studium_key):
        app = self._open_administracia_studia()

        # Vyberieme spravne studium.
        self.__vyber_studium(app, studium_key)

        # Stlacime v menu "Kontrola" -> "Ziskanych kreditov, prehlad hodnotenia".
        with app.collect_operations() as ops:
            app.d.ziskaneMenuItem.click()

        if len(ops) == 0:
            return []

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

    def __open_novy_zapisny_list_dialog(self, app, studium_key):
        # Vyberieme studium.
        self.__vyber_studium(app, studium_key)

        # Klikneme na tlacidlo pridania noveho zapisneho listu.
        with app.collect_operations() as ops:
            app.d.pridatZapisnyListButton.click()
        app.awaited_open_dialog(ops)

    def get_akademicke_roky_noveho_zapisneho_listu(self, studium_key):
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

    def get_roky_studia_noveho_zapisneho_listu(self, studium_key):
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

    def create_zapisny_list(self, studium_key, akademicky_rok, rok_studia):
        '''Creates enrollment list.

        Args:
            studium_key: studium identifier
            akademicky_rok: Academic year of the time range in the form of
                'start/end'. E.g. '2013/2014'. (optional)
            rok_studia: year of the study
        '''
        app = self._open_administracia_studia()

        self.__open_novy_zapisny_list_dialog(app, studium_key)

        # V combo boxe vyberieme rok studia.
        app.d.rocnikComboBox.select(find_option(app.d.rocnikComboBox.options, id=str(rok_studia)))

        # Ak je nastaveny akademicky rok, vyberieme ho v combo boxe.
        if akademicky_rok is not None:
            app.d.rokComboBox.select(find_option(app.d.rokComboBox.options, id=akademicky_rok))

        # Stlacime tlacidlo "OK".
        with app.collect_operations() as ops:
            app.d.enterButton.click()

        # Dialog sa zavrie a vyskoci message box, ze cinnost bola uspesne dokoncena.
        assert_ops(ops, 'closeDialog', 'messageBox')
        app.close_dialog(app.d.name)
        if ops[1].args[0] != 'Činnosť úspešne dokončená.':
            raise AISBehaviorError("AIS displayed an error: {}".format(ops))

    def delete_zapisny_list(self, studium_key, zapisny_list_key):
        '''Deletes enrollment list.

        Args:
            studium_key: studium identifier
            zapisny_list_key: enrollment list identifier
        '''
        app = self._open_administracia_studia()

        # Vyberieme zapisny list.
        self.__vyber_zapisny_list(app, studium_key, zapisny_list_key)

        # Klikneme na tlacidlo zrusenia zapisneho listu.
        with app.collect_operations() as ops:
            app.d.odobratZapisnyListButton.click()

        # Vyskoci confirm box, ci naozaj chceme odstranit zapisny list. Stlacime "Ano".
        assert_ops(ops, 'confirmBox')
        with app.collect_operations() as ops:
            app.confirm_box(2)
