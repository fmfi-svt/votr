
from fladgejt.helpers import CantOpenApplication, decode_key
from fladgejt.structures import Hodnotenie, Priemer


class WebuiHodnoteniaMixin:
    def get_hodnotenia(self, zapisny_list_key):
        try:
            app = self._open_hodnotenia_priemery_app(zapisny_list_key)
        except CantOpenApplication:
            return [[], "Predmety a hodnotenia pre tento zápisný list nie sú dostupné."]

        studium_key, akademicky_rok = decode_key(zapisny_list_key)

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
                             zapisny_list_key=zapisny_list_key)
                  for row in app.d.hodnoteniaTable.all_rows()]
        return [result, None]
        # TODO: Hmm, Fajr mozno pouziva aj 'uznane'

    def get_priemery(self, zapisny_list_key):
        try:
            app = self._open_hodnotenia_priemery_app(zapisny_list_key)
        except CantOpenApplication:
            return [[], "Priemery pre toto štúdium nie sú dostupné."]

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
        return [result, None]
