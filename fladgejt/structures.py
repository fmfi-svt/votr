
from collections import namedtuple


Studium = namedtuple('Studium', [
    'id', 'sp_skratka', 'sp_popis', 'sp_doplnujuce_udaje', 'zaciatok',
    'koniec', 'sp_dlzka', 'sp_cislo', 'rok_studia'])

ZapisnyList = namedtuple('ZapisnyList', [
    'id', 'akademicky_rok', 'rocnik', 'sp_skratka', 'sp_popis', 'datum_zapisu'])

Predmet = namedtuple('Predmet', [
    'id', 'skratka', 'nazov', 'typ_vyucby', 'semester', 'kredit'])

Hodnotenie = namedtuple('Hodnotenie', [
    'id', 'akademicky_rok', 'skratka', 'nazov', 'typ_vyucby', 'semester', 'kredit',
    'hodn_znamka', 'hodn_termin', 'hodn_datum', 'hodn_znamka_popis'])

Priemer = namedtuple('Priemer', [
    'id', 'akademicky_rok', 'nazov', 'semester', 'ziskany_kredit', 'predmetov',
    'neabsolvovanych', 'studijny_priemer', 'vazeny_priemer', 'pokusy_priemer',
    'datum_vypoctu'])

# moznost_prihlasit = 'A'/'N'
Termin = namedtuple('Termin', [
    'id', 'predmet_id', 'datum', 'cas', 'miestnost', 'pocet_prihlasenych',
    'maximalne_prihlasenych', 'hodnotiaci', 'prihlasovanie_od', 'prihlasovanie_do',
    'poznamka', 'moznost_prihlasit'])

# skratka -> skratka studijneho programu
Prihlasena_osoba = namedtuple('Prihlasena_osoba', [
    'skratka', 'datum_prihlasenia', 'plne_meno', 'rocnik'])
