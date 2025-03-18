"""Calls most read-only Fladgejt RPCs."""

from tests.testutils import scenario_main
from votrfront.rpc import encode_result

def run(client):
    def call(name, *args, silent=False):
        client.context.log('scenario', f'{name} started', args)
        client.prepare_for_rpc()
        result = encode_result(getattr(client, name)(*args))
        client.context.log('scenario', f'{name} finished', 'silent' if silent else result)
        return result

    if call('get_som_student'):
        studia = call('get_studia')

        zapisne_listy = []
        for studium in studia:
            sk = studium['studium_key']

            zapisne_listy.extend(call('get_zapisne_listy', sk))

            call('get_prehlad_kreditov', studium['studium_key'])

            # 'get_akademicke_roky_noveho_zapisneho_listu' and
            # 'get_roky_studia_noveho_zapisneho_listu' are omitted because they
            # are currently unused, and do not have proper error reporting if
            # it's currently unavailable.

        for zapisny_list in zapisne_listy:
            zlk = zapisny_list['zapisny_list_key']

            call('zapisny_list_key_to_akademicky_rok', zlk)

            call('get_hodnotenia', zlk)
            call('get_priemery', zlk)
            call('get_priebezne_hodnotenia', zlk)

            if call('get_vidim_terminy_hodnotenia', zlk):
                call('get_predmety', zlk)  # Currently unused.
                prihlasene = call('get_prihlasene_terminy', zlk)
                vypisane = call('get_vypisane_terminy', zlk)
                # get_vypisane_terminy_predmetu is used inside
                # get_vypisane_terminy. No need to test it separately.

                for termin in prihlasene + vypisane:
                    call('get_prihlaseni_studenti', termin['termin_key'])

            call('zapis_get_vlastnosti_programu', zlk)
            call('zapis_ponuka_options', zlk)
            call('zapis_ponuka_vyhladaj', zlk, '', '', '', 'Prog')

            for cast in ['SC', 'SS']:
                call('zapis_get_zapisane_predmety', zlk, cast)
                call('zapis_plan_vyhladaj', zlk, cast)

    roky = call('get_register_osob_akademicky_rok_options')
    call('get_register_osob_fakulty')
    call('vyhladaj_osobu', '', 'a', False, False, False, roky[0]['id'], None, None, False, False, False, False, False, False, False, False, False, False)
    call('vyhladaj_osobu', 'a', '', True, True, True, roky[1]['id'], 'FMFI', 'INF', True, True, True, True, True, True, True, True, True, True)

    call('get_register_predmetov_fakulta_options')
    roky = call('get_register_predmetov_akademicky_rok_options')
    call('get_register_predmetov_semester_options')
    call('get_register_predmetov_stupen_options')
    call('vyhladaj_predmety', roky[0]['id'], None, None, None, None, 'prog', None, None)
    call('vyhladaj_predmety', roky[1]['id'], 'FMFI', 'zle', 'zle', 'bla', 'bla', 'Z', 'I.')
    predmety, _ = call('vyhladaj_predmety', roky[2]['id'], 'FMFI', 'FMFI.KAI', None, None, None, None, None)

    for predmet in predmety[0:5]:
        call('get_informacny_list', predmet['predmet_key'], roky[2]['id'], silent=True)

        _, predmet2 = call('get_studenti_zapisani_na_predmet', predmet['predmet_key'], roky[2]['id'])

        call('get_ucitelia_predmetu', predmet['predmet_key'], roky[2]['id'], predmet2['semester'], predmet2['fakulta'])

    call('get_semester_obdobie', 'Z')
    call('get_semester_obdobie', 'L')
    call('get_skuskove_obdobie', 'Z')
    call('get_skuskove_obdobie', 'L')
    # get_obdobie is used inside those two. No need to test it separately.

    # Omitted RPCs because they are not read-only:
    # - create_zapisny_list
    # - delete_zapisny_list
    # - prihlas_na_termin
    # - odhlas_z_terminu
    # - zapis_plan_pridaj_predmety
    # - zapis_ponuka_pridaj_predmety
    # - zapis_odstran_predmety


if __name__ == '__main__':
    scenario_main(run)
