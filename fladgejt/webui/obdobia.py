# -*- coding: utf-8 -*-

from aisikl.app import Application
from fladgejt.helpers import find_row
from fladgejt.structures import Obdobie
from fladgejt.webui.pool import pooled_app


class WebuiObdobiaMixin:
    @pooled_app
    def _open_sprava_datumov(self):
        '''Opens 'Správa dátumových akcií' application (VSST010).

        :return: a :class:`~Application` object.
        '''
        url = '/ais/servlets/WebUIServlet?appClassName=ais.gui.vs.st.VSST010App' \
              '&fajr=A&kodAplikacie=VSST010&uiLang=SK'
        app, ops = Application.open(self.context, url)
        app.awaited_open_main_dialog(ops)
        return app

    def get_obdobie(self, datumova_akcia_id, akademicky_rok=None):
        '''Returns a time range defined by a given datumova_akcia_id. The
        academic year of such action can be changed with optional parameter
        akademicky_rok.

        Args:
            datumova_akcia_id: The ID of a time range. (Field 'D.a.')
            akademicky_rok: Academic year of the time range in the form of
                'start/end'. E.g. '2013/2014'. (optional)

        Returns:
            A :class:`~Obdobie` object.
        '''
        app = self._open_sprava_datumov()

        # shortname pre 'D.a.' je pochopitelne 'kod'
        index = find_row(app.d.akcieTable.all_rows(), kod=datumova_akcia_id)

        app.d.akcieTable.select(index)

        # ak je, selectneme aj akademicky rok
        if akademicky_rok is not None:
            detail_index = find_row(app.d.detailAkcieTable.all_rows(),
                                    ppopisAkademickyRok=akademicky_rok)
        else:
            detail_index = 0

        row = app.d.detailAkcieTable.all_rows()[detail_index]

        return Obdobie(obdobie_od=row['odDatumu'],
                       obdobie_do=row['doDatumu'],
                       id_akcie=datumova_akcia_id)

    def get_semester_obdobie(self, semester, akademicky_rok=None):
        '''Returns a time range of a given semester.

        Args:
            semester: Either 'L' for spring of 'Z' for fall.
            akademicky_rok: Academic year of the time range in the form of
                'start/end'. E.g. '2013/2014'. (optional)

        Returns:
            A :class:`~Obdobie` object.
        '''
        if semester == "L":
            return self.get_obdobie('07', akademicky_rok)
        elif semester == "Z":
            return self.get_obdobie('05', akademicky_rok)
        else:
            raise ValueError('Wrong type of semester "{0}"'.format(semester))

    def get_skuskove_obdobie(self, semester, akademicky_rok=None):
        '''Returns a time range of a given examination period.

        Args:
            semester: Either 'L' for spring of 'Z' for fall.
            akademicky_rok: Academic year of the time range in the form of
                'start/end'. E.g. '2013/2014'. (optional)

        Returns:
            A :class:`~Obdobie` object.
        '''
        if semester == "L":
            return self.get_obdobie('08', akademicky_rok)
        elif semester == "Z":
            return self.get_obdobie('06', akademicky_rok)
        else:
            raise ValueError('Wrong type of semester "{0}"'.format(semester))
