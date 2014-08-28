
from collections import namedtuple
from .helpers import keyed_namedtuple


Studium = keyed_namedtuple('Studium', [
    'sp_skratka', 'sp_popis', 'sp_doplnujuce_udaje', 'zaciatok', 'koniec',
    'sp_dlzka', 'sp_cislo', 'rok_studia', 'key'],
    ['sp_skratka', 'zaciatok'])

ZapisnyList = keyed_namedtuple('ZapisnyList', [
    'akademicky_rok', 'rocnik', 'sp_skratka', 'sp_popis', 'datum_zapisu',
    'key'],
    ['akademicky_rok'])

Predmet = keyed_namedtuple('Predmet', [
    'skratka', 'nazov', 'typ_vyucby', 'semester', 'kredit', 'key'],
    ['skratka'])

Hodnotenie = namedtuple('Hodnotenie', [
    'akademicky_rok', 'skratka', 'nazov', 'typ_vyucby', 'semester', 'kredit',
    'hodn_znamka', 'hodn_termin', 'hodn_datum', 'hodn_znamka_popis'])

Priemer = namedtuple('Priemer', [
    'akademicky_rok', 'nazov', 'semester', 'ziskany_kredit', 'predmetov',
    'neabsolvovanych', 'studijny_priemer', 'vazeny_priemer', 'pokusy_priemer',
    'datum_vypoctu'])

Termin = keyed_namedtuple('Termin', [
    'datum', 'cas', 'miestnost', 'pocet_prihlasenych', 'maximalne_prihlasenych',
    'hodnotiaci', 'prihlasovanie_od', 'prihlasovanie_do', 'poznamka',
    'moznost_prihlasit', 'key'],
    ['datum', 'cas', 'miestnost', 'poznamka'])

PrihlasenyStudent = namedtuple('PrihlasenyStudent', [
    'skratka', 'datum_prihlasenia', 'plne_meno', 'rocnik'])

Obdobie = namedtuple('Obdobie', ['obdobie_od', 'obdobie_do', 'id_akcie'])
