
from fladgejt.structures import Hodnotenie, Priemer


class WebuiHodnoteniaMixin:
    def get_hodnotenia(self, studijny_program, akademicky_rok):
        app = self._open_hodnotenia_priemery_app(studijny_program, akademicky_rok)

        result = [Hodnotenie(akademicky_rok=akademicky_rok,
                             skratka=row['skratka'],
                             nazov=row['nazov'],
                             typ_vyucby=row['kodTypVyucbySP'],
                             semester=row['semester'],
                             kredit=row['kredit'],
                             hodn_znamka=row['znamka'],
                             hodn_termin=row['termin'],
                             hodn_datum=row['datum'],
                             hodn_znamka_popis=row['znamkaPopis'])
                  for row in app.d.hodnoteniaTable.all_rows()]
        return result
        # TODO: Hmm, Fajr mozno pouziva aj 'uznane'

    def get_priemery(self, studijny_program, akademicky_rok):
        app = self._open_hodnotenia_priemery_app(studijny_program, akademicky_rok)

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
        return result
