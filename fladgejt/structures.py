
from collections import namedtuple


Studium = namedtuple('Studium', [
    'sp_skratka', 'sp_popis', 'sp_doplnujuce_udaje', 'zaciatok', 'koniec',
    'sp_dlzka', 'sp_cislo', 'rok_studia'])

ZapisnyList = namedtuple('ZapisnyList', [
    'akademicky_rok', 'rocnik', 'sp_skratka', 'sp_popis', 'datum_zapisu'])

Predmet = namedtuple('Predmet', [
    'skratka', 'nazov', 'typ_vyucby', 'semester', 'kredit'])

Hodnotenie = namedtuple('Hodnotenie', [
    'akademicky_rok', 'skratka', 'nazov', 'typ_vyucby', 'semester', 'kredit',
    'hodn_znamka', 'hodn_termin', 'hodn_datum', 'hodn_znamka_popis'])

Priemer = namedtuple('Priemer', [
    'akademicky_rok', 'nazov', 'semester', 'ziskany_kredit', 'predmetov',
    'neabsolvovanych', 'studijny_priemer', 'vazeny_priemer', 'pokusy_priemer',
    'datum_vypoctu'])
