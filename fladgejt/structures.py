from fladgejt.helpers import with_key_fields
from typing import TypedDict


@with_key_fields(studium_key=['sp_skratka', 'zaciatok'])
class Studium(TypedDict):
    sp_skratka: str
    sp_popis: str
    sp_doplnujuce_udaje: str
    zaciatok: str
    koniec: str
    sp_dlzka: str
    sp_cislo: str
    rok_studia: str
    organizacna_jednotka: str

@with_key_fields(zapisny_list_key=['studium_key', 'akademicky_rok'])
class ZapisnyList(TypedDict):
    akademicky_rok: str
    rocnik: str
    sp_skratka: str
    sp_popis: str
    datum_zapisu: str
    studium_key: str

@with_key_fields(predmet_key=['skratka'])
class Predmet(TypedDict):
    skratka: str
    nazov: str
    typ_vyucby: str
    semester: str
    kredit: str

@with_key_fields(predmet_key=['skratka'])
class RegPredmet(TypedDict):
    skratka: str
    nazov: str
    konanie: str
    stredisko: str
    fakulta: str
    cudzi_nazov: str
    rozsah_vyucby: str
    semester: str
    kredit: str

@with_key_fields(predmet_key=['skratka'])
class ZapisPredmet(TypedDict):
    skratka: str
    nazov: str
    typ_vyucby: str
    semester: str
    kredit: str
    rozsah_vyucby: str
    jazyk: str
    datum_zapisu: str | None
    aktualnost: str
    pocet_prihlasenych: str | None
    maximalne_prihlasenych: str | None
    blok_skratka: str | None
    blok_nazov: str | None
    blok_index: str | None
    v_bloku_index: str | None
    odporucany_rocnik: str | None
    cast: str

class ZapisVlastnost(TypedDict):
    skratka: str
    nazov: str
    minimalny_kredit: str
    poznamka: str

@with_key_fields(predmet_key=['skratka'])
class Hodnotenie(TypedDict):
    akademicky_rok: str
    skratka: str
    nazov: str
    typ_vyucby: str
    semester: str
    kredit: str
    hodn_znamka: str
    hodn_termin: str
    hodn_datum: str
    hodn_znamka_popis: str
    nahradeny: bool
    poplatok: str
    zapisny_list_key: str

class PriebezneHodnotenie(TypedDict):
    dovod: str
    poc_bodov: str
    maximum: str
    zaevidoval: str
    zapocitavat: str
    minimum: str

@with_key_fields(predmet_key=['skratka'])
class PriebezneHodnoteniaPredmetu(TypedDict):
    akademicky_rok: str
    skratka: str
    nazov: str
    semester: str
    kredit: str
    zaznamy: list[PriebezneHodnotenie]

class Priemer(TypedDict):
    akademicky_rok: str
    nazov: str
    semester: str
    ziskany_kredit: str
    predmetov: str
    neabsolvovanych: str
    studijny_priemer: str
    vazeny_priemer: str
    pokusy_priemer: str
    datum_vypoctu: str

@with_key_fields(
    predmet_key=['skratka_predmetu'],
    termin_key=['zapisny_list_key', 'predmet_key', 'datum', 'cas', 'miestnost', 'poznamka'],
)
class Termin(TypedDict):
    datum: str
    cas: str
    miestnost: str
    pocet_prihlasenych: str
    maximalne_prihlasenych: str
    hodnotiaci: str
    prihlasovanie: str
    odhlasovanie: str
    poznamka: str
    akademicky_rok: str
    nazov_predmetu: str
    skratka_predmetu: str
    moznost_prihlasit: str
    datum_prihlasenia: str
    datum_odhlasenia: str
    hodnotenie_terminu: str
    hodnotenie_predmetu: str
    zapisny_list_key: str

class PrihlasenyStudent(TypedDict):
    sp_skratka: str
    datum_prihlasenia: str
    plne_meno: str
    rocnik: str
    email: str

class Obdobie(TypedDict):
    obdobie_od: str
    obdobie_do: str
    id_akcie: str

class RegUcitelPredmetu(TypedDict):
    plne_meno: str
    typ: str

class RegOsoba(TypedDict):
    meno: str
    priezvisko: str
    plne_meno: str
    email: str
