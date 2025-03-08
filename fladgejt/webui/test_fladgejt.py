# -*- coding: utf-8 -*-

from fladgejt.webui import WebuiOsobyMixin
from fladgejt.webui import WebuiObdobiaMixin
from fladgejt.webui import WebuiPredmetyMixin
from fladgejt.webui import WebuiStudiumMixin
from fladgejt.webui import WebuiTerminyMixin
from fladgejt.webui import WebuiHodnoteniaMixin
from fladgejt.webui import WebuiZapisMixin
from fladgejt.helpers import encode_key, decode_key

class WebuiTestFladgejtMixin:
    
    # je dobry napad definovat si takto globalne premenne?
    
    akademicky_rok = "2018/2019"
    kod_predmetu = ""
    fakulty = "FMFI"
    semester = "L"
    fakulta = "FMFI"
    stredisko = ""
    skratka_sp = ""
    skratka_predmetu = "FMFI.KJFB/1-INF-311/00"
    nazov_predmetu = ""
    stupen = ""
    predmet_key = encode_key((skratka_predmetu,))
    zapisny_list_key = 0
    studium_key = 0
    
    def _test_osoby(self):
            WebuiOsobyMixin.vyhladaj_osobu(self, meno = "", priezvisko =                          
                                    "", absolvent = True, student = True,
                                zamestnanec = True, akademicky_rok = "2018/2019", fakulta = "", studijny_program = "",
                                uchadzaci = False, prvy_rocnik = False, druhy_rocnik = False, treti_rocnik = False,
                                stvrty_rocnik = False, piaty_rocnik = False, siesty_rocnik = False,
                                siedmy_rocnik = False, osmy_rocnik = False, absolventi = False)
            
            WebuiOsobyMixin.get_register_osob_akademicky_rok_options(self)
            
            WebuiOsobyMixin.get_register_osob_fakulty(self)
            return "OK"
        
    def _test_obdobia(self):
            WebuiObdobiaMixin.get_obdobie(self, datumova_akcia_id = "01")
            WebuiObdobiaMixin.get_semester_obdobie(self, self.semester)
            WebuiObdobiaMixin.get_skuskove_obdobie(self, self.semester)
            return "OK"
        
    def _test_predmety(self):
            WebuiPredmetyMixin.get_informacny_list(self, self.kod_predmetu, self.akademicky_rok)
            
            WebuiPredmetyMixin.get_studenti_zapisani_na_predmet(self, self.predmet_key, self.akademicky_rok)
            
            WebuiPredmetyMixin.get_ucitelia_predmetu(self, self.predmet_key, self.akademicky_rok, self.semester, self.fakulty)
            
            WebuiPredmetyMixin.vyhladaj_predmety(self, self.akademicky_rok, self.fakulta, self.stredisko, self.skratka_sp, self.skratka_predmetu, self.nazov_predmetu, self.semester, self.stupen)
            
            WebuiPredmetyMixin.get_register_predmetov_fakulta_options(self)
            
            WebuiPredmetyMixin.get_register_predmetov_akademicky_rok_options(self)
            
            WebuiPredmetyMixin.get_register_predmetov_semester_options(self)
            
            WebuiPredmetyMixin.get_register_predmetov_stupen_options(self)
            return "OK"
        
    def _test_studium(self):
            WebuiStudiumMixin.get_som_student(self)
            studium = WebuiStudiumMixin.get_studia(self)
            self.studium_key = studium[0].studium_key
                
            zapisny_list = WebuiStudiumMixin.get_zapisne_listy(self, self.studium_key)
            
            self.zapisny_list_key = zapisny_list[0].zapisny_list_key

            WebuiStudiumMixin.zapisny_list_key_to_akademicky_rok(self, self.zapisny_list_key)
            
            WebuiStudiumMixin.get_prehlad_kreditov(self, self.studium_key)
            
            WebuiStudiumMixin.get_akademicke_roky_noveho_zapisneho_listu(self, self.studium_key)
            
            WebuiStudiumMixin.get_roky_studia_noveho_zapisneho_listu(self, self.studium_key)
            
            WebuiStudiumMixin.create_zapisny_list(self, self.studium_key, self.akademicky_rok, rok_studia = 1)
            
            WebuiStudiumMixin.delete_zapisny_list(self, self.zapisny_list_key)
            return "OK"
        
        
    def _test_termin(self):
            WebuiTerminyMixin.get_vidim_terminy_hodnotenia(self, self.zapisny_list_key)

            WebuiTerminyMixin.get_predmety(self, self.zapisny_list_key)
            
            WebuiTerminyMixin.get_prihlasene_terminy(self, self.zapisny_list_key)
            
            terminy = WebuiTerminyMixin.get_vypisane_terminy(self, self.zapisny_list_key)
            
            datum = terminy[0].datum
            cas = terminy[0].cas
            miestnost = terminy[0].miestnost
            poznamka = terminy[0].poznamka
            skratka_predmetu = terminy[0].skratka_predmetu
            self.predmet_key = encode_key((skratka_predmetu,))
                
            termin_key = encode_key((self.zapisny_list_key, self.predmet_key, datum, cas, miestnost, poznamka,))
            
            WebuiTerminyMixin.get_vypisane_terminy_predmetu(self, self.zapisny_list_key, self.predmet_key)
            
            WebuiTerminyMixin.get_prihlaseni_studenti(self, termin_key)
            
            WebuiTerminyMixin.odhlas_z_terminu(self, termin_key)
            
            WebuiTerminyMixin.prihlas_na_termin(self, termin_key)
            
            return "OK"
        
    def _test_hodnotenia(self):
            WebuiHodnoteniaMixin.get_hodnotenia(self, self.zapisny_list_key)
            
            WebuiHodnoteniaMixin.get_priemery(self, self.zapisny_list_key)
            
            WebuiHodnoteniaMixin.get_priebezne_hodnotenia(self, self.zapisny_list_key)
            return "OK"
    
    
    def _test_zapis(self):
            cast = ""
            dvojice_typ_vyucby_skratka = []
            filter_skratka = ""
            filter_nazov = ""
            zvolene_skratky = ""
            predmet_key_list = [self.predmet_key]
        
            zapisane_predmety = WebuiZapisMixin.zapis_get_zapisane_predmety(self, self.zapisny_list_key, cast)
            self.predmet_key = encode_key((zapisane_predmety[0][0].skratka,))
            predmet_key_list = [self.predmet_key]
            
            WebuiZapisMixin.zapis_get_vlastnosti_programu(self, self.zapisny_list_key)
            
            WebuiZapisMixin.zapis_plan_vyhladaj(self, self.zapisny_list_key, cast)
            
            WebuiZapisMixin.zapis_plan_pridaj_predmety(self, self.zapisny_list_key, cast, dvojice_typ_vyucby_skratka)
            
            WebuiZapisMixin.zapis_ponuka_vyhladaj(self, self.zapisny_list_key, self.fakulta, self.stredisko, filter_skratka, filter_nazov)
            
            WebuiZapisMixin.zapis_ponuka_pridaj_predmety(self, self.zapisny_list_key, self.fakulta, self.stredisko, filter_skratka, filter_nazov, zvolene_skratky)
            
            WebuiZapisMixin.zapis_ponuka_options(self, self.zapisny_list_key)
            
            WebuiZapisMixin.zapis_odstran_predmety(self, self.zapisny_list_key, cast, predmet_key_list)
            return "OK"
            
        
    def test(self):
        print("Test studium: " + self._test_studium())
        print("Test zapis: " + self._test_zapis())
        print("Test osoby: " + self._test_osoby())
        print("Test obdobia: " + self._test_obdobia())
        print("Test predmety: " + self._test_predmety())
        print("Test hodnotenia: " + self._test_hodnotenia())
        print("Test termin: " + self._test_termin())
