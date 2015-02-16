
from aisikl.app import assert_ops
from fladgejt.helpers import (
    CantOpenApplication, find_row, find_option, encode_key, decode_key)
from fladgejt.structures import ZapisPredmet


UNAVAILABLE = "Zápis predmetov pre tento zápisný list nie je dostupný."


class WebuiZapisMixin:
    def zapis_get_zapisane_predmety(self, zapisny_list_key, cast):
        try:
            app = self._open_zapis_predmetov_app(zapisny_list_key)
        except CantOpenApplication:
            return [[], UNAVAILABLE]

        # Oznacime koren stromu, aby sme videli vsetky predmety.
        app.d.castiZapisnehoListuTree.select('nR/' + cast)

        result = [ZapisPredmet(skratka=row['skratka'],
                               nazov=row['nazov'],
                               typ_vyucby=row['kodTypVyucby'],
                               semester=row['semester'],
                               kredit=row['kredit'],
                               rozsah_vyucby=row['rozsah'],
                               jazyk=row['jazyk'],
                               datum_zapisu=row['datumZapisu'],
                               aktualnost=row['aktualnost'],
                               pocet_prihlasenych=None,
                               maximalne_prihlasenych=None,
                               blok_skratka=row['skratkaBlok'],
                               blok_nazov=row['popisBlok'],
                               blok_index=None,
                               v_bloku_index=None,
                               odporucany_rocnik=None,
                               cast=row['kodCastStPlanu'])
                  for row in app.d.predmetyTable.all_rows()]
        return [result, None]

    def zapis_get_ponukane_predmety(self, zapisny_list_key, cast):
        try:
            app = self._open_zapis_predmetov_app(zapisny_list_key)
        except CantOpenApplication:
            return [[], UNAVAILABLE]

        # AIS ponuka styri dialogy na pridavanie predmetov:
        # (1) "Pridat predmet zo studijneho planu"
        # (2) "Pridat predmet z ponuky predmetov"
        # (3) "Pridat neabsolvovany predmet"
        # (4) "Pridat odporucany predmet"
        # Zoznam ponukanych predmetov sa da zistit cez (1), (2) aj (4). (Pre
        # (2) mozme dat vyhladat vsetky predmety a zoradit ich podla bloku. Ale
        # to je dost pomale.) My pouzivame (1), lebo v tabulke su viacere dobre
        # stlpce, ako odporucany rocnik a "oficialne poradie" predmetov. Lenze
        # tieto stlpce su schovane, takze ich najprv musime zobrazit.

        # Optimalizacia pre SC (Studijna cast): Staci otvorit iba C (Vyberove
        # predmety), mozme vypnut filtrovanie podla typu vyucby a uvidime aj
        # A a B. Ale nesmieme ich tak zapisovat, lebo AIS ich zapise ako C, co
        # na studijnom nemaju radi.

        result = []

        # Skusime kazdy vrchol stromu, co nas zaujima.
        for id, node in app.d.castiZapisnehoListuTree.nodes.items():
            if not node.is_leaf: continue
            if '/' + cast + '/' not in id: continue
            if id in ('nR/SC/A', 'nR/SC/B'): continue

            # Oznacime dany vrchol stromu.
            app.d.castiZapisnehoListuTree.select(id)

            # Stlacime "Pridat predmet zo studijneho planu".
            with app.collect_operations() as ops:
                app.d.pridatPredmetAction.execute()

            # Mozno vyskoci chyba.
            if len(ops) == 1 and ops[0].method == 'messageBox':
                return [[], ops[0].args[0]]

            # Mozno vyskoci ze ziadny zaznam.
            # TODO: Zislo by sa to ignorovanie konkretnych messageboxov.
            if len(ops) == 2:
                assert_ops(ops, 'openDialog', 'messageBox')
                if ops[1].args[0] != 'Podmienkam nevyhovuje žiadny záznam.':
                    raise AISBehaviorError("AIS displayed an error: {}".format(ops))
                ops = ops[0:1]

            # Otvori sa novy dialog.
            app.awaited_open_dialog(ops)

            # Zapneme schovane stlpce.
            want = ['kodTypVyucby', 'popis', 'poradieB', 'poradieP', 'kodCastSP']
            if any(col not in app.d.predmetyTable.column_map for col in want):
                self._show_all_columns(app, app.d.predmetyTable)

            # Zrusime filter podla odporucaneho rocniku.
            index = find_option(app.d.rocnikComboBox.options, title='')
            app.d.rocnikComboBox.select(index)

            # Ak sa da, zrusime filter podla typu vyucby.
            if app.d.typComboBox.is_really_enabled():
                index = find_option(app.d.typComboBox.options, title='')
                app.d.typComboBox.select(index)

            # Nacitame vsetky predmety.
            with app.collect_operations() as ops:
                app.d.zobrazitPredmetyButton.click()
            if ops:
                assert_ops(ops, 'messageBox')
                if ops[0].args[0] != 'Podmienkam nevyhovuje žiadny záznam.':
                    raise AISBehaviorError("AIS displayed an error: {}".format(ops))

            result.extend(ZapisPredmet(skratka=row['skratkaPredmet'],
                                       nazov=row['nazovPredmet'],
                                       typ_vyucby=row['kodTypVyucby'],
                                       semester=row['kodSemester'],
                                       kredit=row['kredit'],
                                       rozsah_vyucby=row['rozsah'],
                                       jazyk=row['jazyk'],
                                       datum_zapisu=None,
                                       aktualnost=row['kodAktualnost'],
                                       pocet_prihlasenych=row['pocetStudentov'],
                                       maximalne_prihlasenych=row['obmedzenie'],
                                       blok_skratka=row['skratkaBlok'],
                                       blok_nazov=row['popis'],
                                       blok_index=row['poradieB'],
                                       v_bloku_index=row['poradieP'],
                                       odporucany_rocnik=row['rocnik'],
                                       cast=row['kodCastSP'])
                          for row in app.d.predmetyTable.all_rows())

            # Ked sme hotovi, zavrieme dialog.
            with app.collect_operations() as ops:
                app.d.click_close_button()
            app.awaited_close_dialog(ops)

        return [result, None]
