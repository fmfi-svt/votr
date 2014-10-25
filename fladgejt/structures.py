
from collections import namedtuple
from .helpers import keyed_namedtuple


Studium = keyed_namedtuple('Studium', [
    'sp_skratka', 'sp_popis', 'sp_doplnujuce_udaje', 'zaciatok', 'koniec',
    'sp_dlzka', 'sp_cislo', 'rok_studia', 'key'],
    key=['sp_skratka', 'zaciatok'])

ZapisnyList = keyed_namedtuple('ZapisnyList', [
    'akademicky_rok', 'rocnik', 'sp_skratka', 'sp_popis', 'datum_zapisu',
    'key'],
    key=['akademicky_rok'])

Predmet = keyed_namedtuple('Predmet', [
    'skratka', 'nazov', 'typ_vyucby', 'semester', 'kredit', 'key'],
    key=['skratka'])

RegPredmet = keyed_namedtuple('RegPredmet', [
    'skratka', 'nazov', 'konanie', 'stredisko', 'fakulta', 'cudzi_nazov',
    'rozsah_vyucby', 'semester', 'kredit', 'key'], key=['skratka'])

Hodnotenie = keyed_namedtuple('Hodnotenie', [
    'akademicky_rok', 'skratka', 'nazov', 'typ_vyucby', 'semester', 'kredit',
    'hodn_znamka', 'hodn_termin', 'hodn_datum', 'hodn_znamka_popis', 'key'],
    key=['skratka'])

Priemer = namedtuple('Priemer', [
    'akademicky_rok', 'nazov', 'semester', 'ziskany_kredit', 'predmetov',
    'neabsolvovanych', 'studijny_priemer', 'vazeny_priemer', 'pokusy_priemer',
    'datum_vypoctu'])

Termin = keyed_namedtuple('Termin', [
    'datum', 'cas', 'miestnost', 'pocet_prihlasenych', 'maximalne_prihlasenych',
    'hodnotiaci', 'prihlasovanie', 'odhlasovanie', 'poznamka', 'akademicky_rok',
    'nazov_predmetu', 'skratka_predmetu', 'moznost_prihlasit',
    'hodnotenie_terminu', 'hodnotenie_predmetu', 'key', 'predmet_key'],
    key=['datum', 'cas', 'miestnost', 'poznamka'],
    predmet_key=['skratka_predmetu'])

PrihlasenyStudent = namedtuple('PrihlasenyStudent', [
    'sp_skratka', 'datum_prihlasenia', 'plne_meno', 'rocnik', 'email'])

Obdobie = namedtuple('Obdobie', ['obdobie_od', 'obdobie_do', 'id_akcie'])

RegUcitelPredmetu = namedtuple('RegUcitelPredmetu', ['plne_meno', 'typ'])
