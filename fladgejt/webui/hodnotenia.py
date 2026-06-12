from fladgejt.helpers import CantOpenApplication, decode_key
from fladgejt.structures import Hodnotenie, Priemer, PriebezneHodnotenie, PriebezneHodnoteniaPredmetu
from fladgejt.webui.studium import WebuiStudiumMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from abc import ABC
    from aisikl.components.button import Button
    from aisikl.components.table import Table
    from aisikl.dialog import Dialog

    class HodnoteniaPriemeryDialogsType(ABC, Dialog):
        hodnoteniaTable: Table
        priemeryTable: Table
        refreshButton: Button

    class PriebezneHodnotenieDialogsType(ABC, Dialog):
        hodnotenieTable: Table
        nacitatHodnotenieButton: Button
        predmetySPriebeznymHodnotenimTable: Table
        refreshButton: Button
else:
    HodnoteniaPriemeryDialogsType = None
    PriebezneHodnotenieDialogsType = None


class WebuiHodnoteniaMixin(WebuiStudiumMixin):
    def get_hodnotenia(self, zapisny_list_key: str) -> tuple[list[Hodnotenie], str | None]:
        try:
            app = self._open_hodnotenia_priemery_app(zapisny_list_key)
        except CantOpenApplication:
            return ([], "Predmety a hodnotenia pre tento zápisný list nie sú dostupné.")

        # Ak uz bola aplikacia otvorena pred tymto volanim, stlacime "Refresh".
        if getattr(app, 'freshly_opened', True):
            app.freshly_opened = False  # pyrefly: ignore [missing-attribute] # pyright: ignore [reportAttributeAccessIssue]
        else:
            app.d.refreshButton.click()

        _studium_key, akademicky_rok = decode_key(zapisny_list_key)

        result = [Hodnotenie(akademicky_rok=akademicky_rok,
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
                             zapisny_list_key=zapisny_list_key)
                  for row in app.d.hodnoteniaTable.all_rows()]
        return (result, None)

    def get_priemery(self, zapisny_list_key: str) -> tuple[list[Priemer], str | None]:
        try:
            app = self._open_hodnotenia_priemery_app(zapisny_list_key)
        except CantOpenApplication:
            return ([], "Priemery pre toto štúdium nie sú dostupné.")

        app.freshly_opened = False  # pyrefly: ignore [missing-attribute] # pyright: ignore [reportAttributeAccessIssue]

        result = [Priemer(akademicky_rok=row['priemerInfoPopisAkadRok'],
                          nazov=row['priemerNazov'],
                          semester=row['semesterKodJ'],
                          ziskany_kredit=row['ziskanyKredit'],
                          predmetov=row['pocetPredmetov'],
                          neabsolvovanych=row['pocetNeabs'],
                          studijny_priemer=row['studPriemer'],
                          vazeny_priemer=row['vazPriemer'],
                          pokusy_priemer=row['pokusyPriemer'],
                          datum_vypoctu=row['priemerInfoDatum'])
                  for row in app.d.priemeryTable.all_rows()]
        return (result, None)

    def get_priebezne_hodnotenia(self, zapisny_list_key: str) -> tuple[list[PriebezneHodnoteniaPredmetu], str | None]:
        try:
            app = self._open_priebezne_hodnotenie_app(zapisny_list_key)
        except CantOpenApplication:
            return ([], "Priebežné hodnotenia pre tento zápisný list nie sú dostupné.")

        # Ak uz bola aplikacia otvorena pred tymto volanim, stlacime "Refresh".
        if getattr(app, 'freshly_opened', True):
            app.freshly_opened = False  # pyrefly: ignore [missing-attribute] # pyright: ignore [reportAttributeAccessIssue]
        else:
            app.d.refreshButton.click()

        _studium_key, akademicky_rok = decode_key(zapisny_list_key)

        result: list[PriebezneHodnoteniaPredmetu] = []
        for i, row in enumerate(app.d.predmetySPriebeznymHodnotenimTable.all_rows()):
            # Klikneme na predmet s priebeznym hodnotenim a pockame na nacitanie
            with app.collect_operations() as ops:
                app.d.predmetySPriebeznymHodnotenimTable.select(i)
            if ops:
                app.awaited_refresh_dialog(ops)

            # Klikneme na button nacitatHodnotenie
            app.d.nacitatHodnotenieButton.click()

            records = [PriebezneHodnotenie(dovod=prow['dovod'],
                                           poc_bodov=prow['pocetBodov'],
                                           maximum=prow['dovodPriebHodHranica'],
                                           zaevidoval=prow['zapisalPlneMeno'],
                                           zapocitavat=prow['zapocitat'],
                                           minimum=prow['dovodPriebHodMinHranica'])
                       for prow in app.d.hodnotenieTable.all_rows()]

            result.append(PriebezneHodnoteniaPredmetu(akademicky_rok=akademicky_rok,
                                                      skratka=row['skratka'],
                                                      nazov=row['predmetNazov'],
                                                      kredit=row['kredit'],
                                                      semester=row['semesterKodJ'],
                                                      zaznamy=records))
        return (result, None)
