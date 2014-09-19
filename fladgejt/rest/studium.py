
from fladgejt.helpers import with_key_args
from fladgejt.structures import Studium, ZapisnyList


class RestStudiumMixin:
    def get_studia(self):
        studia = self.context.request_json('/studium')

        result = [Studium(sp_skratka=row['studijnyProgramSkratka'],
                          sp_popis=row['studijnyProgramPopis'],
                          sp_doplnujuce_udaje=row['studijnyProgramDoplnujuceUdaje'],
                          zaciatok=row['zaciatokStudia'],
                          koniec=row['koniecStudia'],
                          sp_dlzka=row['studijnyProgramDlzka'],
                          sp_cislo=row['studijnyProgramIdProgramCRS'],
                          rok_studia=row['rokStudia']) 
                  for row in studia]
        return result

    @with_key_args(True)
    def get_zapisne_listy(self, studium_key):
        sp_skratka, zaciatok = studium_key

        zapisne_listy = self.context.request_json(
            "/studium/zapisneListy",
            skratkaStudijnehoProgramu=sp_skratka,
            zaciatokStudia=zaciatok)

        result = [ZapisnyList(akademicky_rok=row['popisAkadRok'],
                              rocnik=row['rokRocnik'],
                              sp_skratka=row['studProgramSkratka'],
                              sp_popis=row['studProgramPopis'],
                              datum_zapisu=row['datumZapisu'])
                  for row in zapisne_listy]

        return result
