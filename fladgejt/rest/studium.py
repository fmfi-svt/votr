from fladgejt.base import BaseClient
from fladgejt.helpers import decode_key
from fladgejt.structures import Studium, ZapisnyList


def convert(rows: list[dict[str, object]]) -> list[dict[str, str]]:
    # For now, votrfront expects all columns to be strings, not numbers or null.
    return [{ k: '' if v is None else str(v) for k, v in row.items() } for row in rows]


class RestStudiumMixin(BaseClient):
    def get_studia(self) -> list[Studium]:
        studia = convert(self.context.request_json('studium'))

        result = [Studium(sp_skratka=row['studijnyProgramSkratka'],
                          sp_popis=row['studijnyProgramPopis'],
                          sp_doplnujuce_udaje=row['studijnyProgramDoplnujuceUdaje'],
                          zaciatok=row['zaciatokStudia'],
                          koniec=row['koniecStudia'],
                          sp_dlzka=row['studijnyProgramDlzka'],
                          sp_cislo=row['studijnyProgramIdProgramCRS'],
                          rok_studia=row['rokStudia'],
                          organizacna_jednotka=row['organizacnaJednotka'])
                  for row in studia]
        return result

    def get_zapisne_listy(self, studium_key: str) -> list[ZapisnyList]:
        sp_skratka, zaciatok = decode_key(studium_key)

        zapisne_listy = convert(self.context.request_json(
            "studium/zapisneListy",
            skratkaStudijnehoProgramu=sp_skratka,
            zaciatokStudia=zaciatok))

        result = [ZapisnyList(akademicky_rok=row['popisAkadRok'],
                              rocnik=row['rokRocnik'],
                              sp_skratka=row['studProgramSkratka'],
                              sp_popis=row['studProgramPopis'],
                              datum_zapisu=row['datumZapisu'],
                              studium_key=studium_key)
                  for row in zapisne_listy]

        return result
