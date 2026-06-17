"""Calls most read-only Fladgejt RPCs."""

from tests.testutils import scenario_main
from votrfront.rpc import encode_result

async def run(client):
    async def call(name, *args, silent=False):
        await client.context.log('scenario', f'{name} started', args)
        await client.prepare_for_rpc()
        result = encode_result(await getattr(client, name)(*args))
        await client.context.log('scenario', f'{name} finished', 'silent' if silent else result)
        return result

    if await call('get_som_student'):
        studia = await call('get_studia')

        zapisne_listy = []
        for studium in studia:
            sk = studium['studium_key']

            zapisne_listy.extend(await call('get_zapisne_listy', sk))

            await call('get_prehlad_kreditov', studium['studium_key'])

            # 'get_akademicke_roky_noveho_zapisneho_listu' and
            # 'get_roky_studia_noveho_zapisneho_listu' are omitted because they
            # are currently unused, and do not have proper error reporting if
            # it's currently unavailable.

        for zapisny_list in zapisne_listy:
            zlk = zapisny_list['zapisny_list_key']

            await call('zapisny_list_key_to_akademicky_rok', zlk)

            await call('get_hodnotenia', zlk)
            await call('get_priemery', zlk)
            await call('get_priebezne_hodnotenia', zlk)

            if await call('get_vidim_terminy_hodnotenia', zlk):
                await call('get_predmety', zlk)  # Currently unused.
                prihlasene = await call('get_prihlasene_terminy', zlk)
                vypisane = await call('get_vypisane_terminy', zlk)
                # get_vypisane_terminy_predmetu is used inside
                # get_vypisane_terminy. No need to test it separately.

                for termin in prihlasene + vypisane:
                    await call('get_prihlaseni_studenti', termin['termin_key'])

            await call('zapis_get_vlastnosti_programu', zlk)
            await call('zapis_ponuka_options', zlk)
            await call('zapis_ponuka_vyhladaj', zlk, '', '', '', 'Prog')

            for cast in ['SC', 'SS']:
                await call('zapis_get_zapisane_predmety', zlk, cast)
                await call('zapis_plan_vyhladaj', zlk, cast)

    roky = await call('get_register_osob_akademicky_rok_options')
    await call('get_register_osob_fakulty')
    await call('vyhladaj_osobu', '', 'a', False, False, False, roky[0]['id'], None, None, False, False, False, False, False, False, False, False, False, False)
    await call('vyhladaj_osobu', 'a', '', True, True, True, roky[1]['id'], 'FMFI', 'INF', True, True, True, True, True, True, True, True, True, True)

    await call('get_register_predmetov_fakulta_options')
    roky = await call('get_register_predmetov_akademicky_rok_options')
    await call('get_register_predmetov_semester_options')
    await call('get_register_predmetov_stupen_options')
    await call('vyhladaj_predmety', roky[0]['id'], None, None, None, None, 'prog', None, None)
    await call('vyhladaj_predmety', roky[1]['id'], 'FMFI', 'zle', 'zle', 'bla', 'bla', 'Z', 'I.')
    predmety, _ = await call('vyhladaj_predmety', roky[2]['id'], 'FMFI', 'FMFI.KAI', None, None, None, None, None)

    for predmet in predmety[0:5]:
        await call('get_informacny_list', predmet['predmet_key'], roky[2]['id'], silent=True)

        predmet2 = (await call('get_studenti_zapisani_na_predmet', predmet['predmet_key'], roky[2]['id']))['predmet']

        await call('get_ucitelia_predmetu', predmet['predmet_key'], roky[2]['id'], predmet2['semester'], predmet2['fakulta'])

    await call('get_semester_obdobie', 'Z')
    await call('get_semester_obdobie', 'L')
    await call('get_skuskove_obdobie', 'Z')
    await call('get_skuskove_obdobie', 'L')
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
