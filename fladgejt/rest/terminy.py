
from fladgejt.helpers import decode_key
from fladgejt.structures import Predmet, Termin


class RestTerminyMixin:
    def get_predmety(self, zapisny_list_key):
        studium_key, akademicky_rok = decode_key(zapisny_list_key)
        sp_skratka, zaciatok = decode_key(studium_key)

        predmety = self.context.request_json(
            "zapisnyList/predmety",
            skratkaStudijnehoProgramu=sp_skratka,
            zaciatokStudia=zaciatok,
            akademickyRok=akademicky_rok)

        result = [Predmet(skratka=row['skratka'],
                          nazov=row['nazov'],
                          typ_vyucby=row['kodTypVyucby'],
                          semester=row['semester'],
                          kredit=row['kredit'])
                  for row in predmety]
        return result

    def get_prihlasene_terminy(self, zapisny_list_key):
        studium_key, akademicky_rok = decode_key(zapisny_list_key)
        sp_skratka, zaciatok = decode_key(studium_key)

        terminy = self.context.request_json(
            "zapisnyList/terminyHodnotenia",
            skratkaStudijnehoProgramu=sp_skratka,
            zaciatokStudia=zaciatok,
            akademickyRok=akademicky_rok)

        result = [Termin(datum=row['dat'],
                         cas=row['cas'],
                         miestnost=row['miestnosti'],
                         pocet_prihlasenych=row['pocetPrihlasenych'],
                         maximalne_prihlasenych=row['maxPocet'],
                         hodnotiaci=row['hodnotiaci'],
                         prihlasovanie=row['prihlasovanie'],
                         odhlasovanie=row['odhlasovanie'],
                         poznamka=row['poznamka'],
                         skratka_predmetu=row['skratkaPredmetu'],
                         nazov_predmetu=row['nazovPredmetu'],
                         hodnotenie_terminu=row['hodnotenieTerminu'],
                         hodnotenie_predmetu=row['hodnoteniePredmetu'],
                         moznost_prihlasit=row['moznostPrihlasenia'],
                         datum_prihlasenia=row['datumPrihlasenia'],
                         datum_odhlasenia=row['datumOdhlasenia'],
                         akademicky_rok=akademicky_rok,
                         zapisny_list_key=zapisny_list_key)
                  for row in terminy
                  if not row['datumOdhlasenia']]
        return result

    def get_vypisane_terminy(self, zapisny_list_key):
        predmety = self.get_predmety(zapisny_list_key)

        result = []

        for row in predmety:
            result.extend(self.get_vypisane_terminy_predmetu(
                zapisny_list_key, row.predmet_key))

        return result

    def get_vypisane_terminy_predmetu(self, zapisny_list_key, predmet_key):
        studium_key, akademicky_rok = decode_key(zapisny_list_key)
        sp_skratka, zaciatok = decode_key(studium_key)
        (skratka,) = decode_key(predmet_key)

        terminy = self.context.request_json(
            "predmet/aktualneTerminyHodnotenia",
            skratkaStudijnehoProgramu=sp_skratka,
            zaciatokStudia=zaciatok,
            akademickyRok=akademicky_rok,
            skratkaPredmetu=skratka)

        result = [Termin(datum=row['dat'],
                         cas=row['cas'],
                         miestnost=row['miestnosti'],
                         pocet_prihlasenych=row['pocetPrihlasenych'],
                         maximalne_prihlasenych=row['maxPocet'],
                         hodnotiaci=row['hodnotiaci'],
                         prihlasovanie=row['prihlasovanie'],
                         odhlasovanie=row['odhlasovanie'],
                         poznamka=row['poznamka'],
                         skratka_predmetu=row['skratkaPredmetu'],
                         nazov_predmetu=row['nazovPredmetu'],
                         hodnotenie_terminu=row['hodnotenieTerminu'],
                         hodnotenie_predmetu=row['hodnoteniePredmetu'],
                         moznost_prihlasit=row['moznostPrihlasenia'],
                         datum_prihlasenia="",
                         datum_odhlasenia="",
                         akademicky_rok=akademicky_rok,
                         zapisny_list_key=zapisny_list_key)
                  for row in terminy]

        return result
