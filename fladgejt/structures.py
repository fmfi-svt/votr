
import attr
from .helpers import key_attrib


@attr.attrs(frozen=True, slots=True, kw_only=True)
class Studium:
    sp_skratka = attr.attrib()
    sp_popis = attr.attrib()
    sp_doplnujuce_udaje = attr.attrib()
    zaciatok = attr.attrib()
    koniec = attr.attrib()
    sp_dlzka = attr.attrib()
    sp_cislo = attr.attrib()
    rok_studia = attr.attrib()
    organizacna_jednotka = attr.attrib()
    studium_key = key_attrib('sp_skratka', 'zaciatok')

@attr.attrs(frozen=True, slots=True, kw_only=True)
class ZapisnyList:
    akademicky_rok = attr.attrib()
    rocnik = attr.attrib()
    sp_skratka = attr.attrib()
    sp_popis = attr.attrib()
    datum_zapisu = attr.attrib()
    studium_key = attr.attrib()
    zapisny_list_key = key_attrib('studium_key', 'akademicky_rok')

@attr.attrs(frozen=True, slots=True, kw_only=True)
class Predmet:
    skratka = attr.attrib()
    nazov = attr.attrib()
    typ_vyucby = attr.attrib()
    semester = attr.attrib()
    kredit = attr.attrib()
    predmet_key = key_attrib('skratka')

@attr.attrs(frozen=True, slots=True, kw_only=True)
class RegPredmet:
    skratka = attr.attrib()
    nazov = attr.attrib()
    konanie = attr.attrib()
    stredisko = attr.attrib()
    fakulta = attr.attrib()
    cudzi_nazov = attr.attrib()
    rozsah_vyucby = attr.attrib()
    semester = attr.attrib()
    kredit = attr.attrib()
    predmet_key = key_attrib('skratka')

@attr.attrs(frozen=True, slots=True, kw_only=True)
class ZapisPredmet:
    skratka = attr.attrib()
    nazov = attr.attrib()
    typ_vyucby = attr.attrib()
    semester = attr.attrib()
    kredit = attr.attrib()
    rozsah_vyucby = attr.attrib()
    jazyk = attr.attrib()
    datum_zapisu = attr.attrib()
    aktualnost = attr.attrib()
    pocet_prihlasenych = attr.attrib()
    maximalne_prihlasenych = attr.attrib()
    blok_skratka = attr.attrib()
    blok_nazov = attr.attrib()
    blok_index = attr.attrib()
    v_bloku_index = attr.attrib()
    odporucany_rocnik = attr.attrib()
    cast = attr.attrib()
    predmet_key = key_attrib('skratka')

@attr.attrs(frozen=True, slots=True, kw_only=True)
class ZapisVlastnost:
    skratka = attr.attrib()
    nazov = attr.attrib()
    minimalny_kredit = attr.attrib()
    poznamka = attr.attrib()

@attr.attrs(frozen=True, slots=True, kw_only=True)
class Hodnotenie:
    akademicky_rok = attr.attrib()
    skratka = attr.attrib()
    nazov = attr.attrib()
    typ_vyucby = attr.attrib()
    semester = attr.attrib()
    kredit = attr.attrib()
    hodn_znamka = attr.attrib()
    hodn_termin = attr.attrib()
    hodn_datum = attr.attrib()
    hodn_znamka_popis = attr.attrib()
    zapisny_list_key = attr.attrib()
    predmet_key = key_attrib('skratka')
    hodn_key = key_attrib('zapisny_list_key', 'skratka')

@attr.attrs(frozen=True, slots=True, kw_only=True)
class PriebezneHodnotenie:
    dovod = attr.attrib()
    poc_bodov = attr.attrib()
    maximum = attr.attrib()
    zaevidoval = attr.attrib()
    zapocitavat = attr.attrib()
    minimum = attr.attrib()

@attr.attrs(frozen=True, slots=True, kw_only=True)
class PriebezneHodnoteniaPredmetu:
    akademicky_rok = attr.attrib()
    skratka = attr.attrib()
    nazov = attr.attrib()
    semester = attr.attrib()
    kredit = attr.attrib()
    zaznamy = attr.attrib()
    predmet_key = key_attrib('skratka')

@attr.attrs(frozen=True, slots=True, kw_only=True)
class Priemer:
    akademicky_rok = attr.attrib()
    nazov = attr.attrib()
    semester = attr.attrib()
    ziskany_kredit = attr.attrib()
    predmetov = attr.attrib()
    neabsolvovanych = attr.attrib()
    studijny_priemer = attr.attrib()
    vazeny_priemer = attr.attrib()
    pokusy_priemer = attr.attrib()
    datum_vypoctu = attr.attrib()

@attr.attrs(frozen=True, slots=True, kw_only=True)
class Termin:
    datum = attr.attrib()
    cas = attr.attrib()
    miestnost = attr.attrib()
    pocet_prihlasenych = attr.attrib()
    maximalne_prihlasenych = attr.attrib()
    hodnotiaci = attr.attrib()
    prihlasovanie = attr.attrib()
    odhlasovanie = attr.attrib()
    poznamka = attr.attrib()
    akademicky_rok = attr.attrib()
    nazov_predmetu = attr.attrib()
    skratka_predmetu = attr.attrib()
    moznost_prihlasit = attr.attrib()
    datum_prihlasenia = attr.attrib()
    datum_odhlasenia = attr.attrib()
    hodnotenie_terminu = attr.attrib()
    hodnotenie_predmetu = attr.attrib()
    zapisny_list_key = attr.attrib()
    predmet_key = key_attrib('skratka_predmetu')
    termin_key = key_attrib('zapisny_list_key', 'predmet_key', 'datum', 'cas',
                            'miestnost', 'poznamka')

@attr.attrs(frozen=True, slots=True, kw_only=True)
class PrihlasenyStudent:
    sp_skratka = attr.attrib()
    datum_prihlasenia = attr.attrib()
    plne_meno = attr.attrib()
    rocnik = attr.attrib()
    email = attr.attrib()

@attr.attrs(frozen=True, slots=True, kw_only=True)
class Obdobie:
    obdobie_od = attr.attrib()
    obdobie_do = attr.attrib()
    id_akcie = attr.attrib()

@attr.attrs(frozen=True, slots=True, kw_only=True)
class RegUcitelPredmetu:
    plne_meno = attr.attrib()
    typ = attr.attrib()

@attr.attrs(frozen=True, slots=True, kw_only=True)
class RegOsoba:
    meno = attr.attrib()
    priezvisko = attr.attrib()
    plne_meno = attr.attrib()
    email = attr.attrib()
