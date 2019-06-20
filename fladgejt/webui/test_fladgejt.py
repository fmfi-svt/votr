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
    zapisny_list_key
    studium_key
    
    def _test_osoby(self):
        try:
            WebuiOsobyMixin.vyhladaj_osobu(self, meno = "", priezvisko =                          
                                    "", absolvent = True, student = True,
                                zamestnanec = True, akademicky_rok, fakulta, studijny_program = "",
                                uchadzaci = False, prvy_rocnik = False, druhy_rocnik = False, treti_rocnik = False,
                                stvrty_rocnik = False, piaty_rocnik = False, siesty_rocnik = False,
                                siedmy_rocnik = False, osmy_rocnik = False, absolventi = False)
            
            WebuiOsobyMixin.get_register_osob_akademicky_rok_options(self)
            
            WebuiOsobyMixin.get_register_osob_fakulty(self)
        except StandardError:
            return "StandardError"
        return "OK"
        
    def _test_obdobia(self):
        try:
            WebuiObdobiaMixin.get_obdobie(self, datumova_akcia_id = "01")
            WebuiObdobiaMixin.get_semester_obdobie(self, semester)
            WebuiObdobiaMixin.get_skuskove_obdobie(self, semester)
        except StandardError:
            return "StandardError"
        return "OK"
        
    def _test_predmety(self):
        try:
            WebuiPredmetyMixin.get_informacny_list(self, kod_predmetu,
                                                akademicky_rok)
            WebuiPredmetyMixin.get_studenti_zapisani_na_predmet(self,
                                        predmet_key, akademicky_rok)
            WebuiPredmetyMixin.get_ucitelia_predmetu(self, predmet_key,
                                    akademicky_rok, semester, fakulty)
            WebuiPredmetyMixin.vyhladaj_predmety(self, akademicky_rok,
                                fakulta, stredisko, skratka_sp, skratka_predmetu, nazov_predmetu, semester, stupen)
            WebuiPredmetyMixin.get_register_predmetov_fakulta_options(self)
            WebuiPredmetyMixin.get_register_predmetov_akademicky_rok_options(self)
            WebuiPredmetyMixin.get_register_predmetov_semester_options(self)
            WebuiPredmetyMixin.get_register_predmetov_stupen_options(self)
        except StandardError:
            return "StandardError"
        return "OK"
        
    def _test_studium(self):
        try:
            WebuiStudiumMixin.get_som_student(self)
            studium = WebuiStudiumMixin.get_studia(self)
            studium_key = studium[0].studium_key
                
            zapisny_list = WebuiStudiumMixin.get_zapisne_listy(self,
                                                        studium_key)
            zapisny_list_key = zapisny_list[0].zapisny_list_key

            WebuiStudiumMixin.zapisny_list_key_to_akademicky_rok(self,
                                                    zapisny_list_key)
            WebuiStudiumMixin.get_prehlad_kreditov(self, studium_key)
            WebuiStudiumMixin.get_akademicke_roky_noveho_zapisneho_listu(self, 
                                                            studium_key)
            WebuiStudiumMixin.get_roky_studia_noveho_zapisneho_listu(self,
                                                            studium_key)
            WebuiStudiumMixin.create_zapisny_list(self, studium_key,
                                            akademicky_rok, rok_studia)
            WebuiStudiumMixin.delete_zapisny_list(self, zapisny_list_key)
        except KeyError:
            return "KeyError"
        except StandardError:
            return "StandardError"
        return "OK"
        
        
    def _test_termin(self):
        try:
            WebuiTerminyMixin.get_vidim_terminy_hodnotenia(self,
                                                zapisny_list_key)
            predmety = WebuiTerminyMixin.get_predmety(self,zapisny_list_key)
            predmet_key = predmety[0].predmet_key
            
            WebuiTerminyMixin.get_prihlasene_terminy(self, zapisny_list_key)
            terminy = WebuiTerminyMixin.get_vypisane_terminy(self,
                                                zapisny_list_key)
            WebuiTerminyMixin.get_vypisane_terminy_predmetu(self,
                                            zapisny_list_key, predmet_key)
            
            zapisny_list_key = terminy[0].zapisny_list_key
            predmet_key = terminy[0].predmet_key
            datum = terminy[0].datum
            cas = terminy[0].cas
            miestnost = terminy[0].miestnost
            poznamka = terminy[0].poznamka
                
            termin_key = encode_key((zapisny_list_key, predmet_key, datum,
                                    cas, miestnost, poznamka,))
            WebuiTerminyMixin.get_prihlaseni_studenti(self, termin_key)
            WebuiTerminyMixin.prihlas_na_termin(self, termin_key)
            WebuiTerminyMixin.odhlas_z_terminu(self, termin_key)
        except KeyError:
            return "KeyError"
        except StandardError:
            return "StandardError"
        
    def _test_hodnotenia(self):
        try:
            WebuiHodnoteniaMixin.get_hodnotenia(self, zapisny_list_key)
            WebuiHodnoteniaMixin.get_priemery(self, zapisny_list_key)
            WebuiHodnoteniaMixin.get_priebezne_hodnotenia(self,
                                                zapisny_list_key)
        except StandardError:
            return "StandardError"
        return "OK"
        
    def _test_zapis(self):
        cast = ""
        dvojice_typ_vyucby_skratka = []
        filter_skratka = ""
        filter_nazov = ""
        zvolene_skratky = ""
        predmet_key_list = [predmet_key]
        try:
            WebuiZapisMixin.zapis_get_zapisane_predmety(self,
                                            zapisny_list_key, cast)
            WebuiZapisMixin.zapis_get_vlastnosti_programu(self,
                                                    zapisny_list_key)
            WebuiZapisMixin.zapis_plan_vyhladaj(self, zapisny_list_key, cast)
            WebuiZapisMixin.zapis_plan_pridaj_predmety(self,
                        zapisny_list_key, cast, dvojice_typ_vyucby_skratka)
            WebuiZapisMixin.zapis_ponuka_vyhladaj(self, zapisny_list_key,
                        fakulta, stredisko, filter_skratka, filter_nazov)
            WebuiZapisMixin.zapis_ponuka_pridaj_predmety(self,
                        zapisny_list_key, fakulta, stredisko,
                        filter_skratka, filter_nazov, zvolene_skratky)
            WebuiZapisMixin.zapis_ponuka_options(self, zapisny_list_key)
            WebuiZapisMixin.zapis_odstran_predmety(self, zapisny_list_key,
                                               cast, predmet_key_list)
        except StandardError:
            return "StandardError"
        return "OK"
            
        
    def test(self):
        print("Test zapis: " + _test_zapis())
        print("Test osoby: " + _test_osoby())
        print("Test obdobia: " + _test_obdobia())
        print("Test predmety: " + _test_predmety())
        print("Test hodnotenia: " + _test_hodnotenia())
        print("Test studium: " + _test_studium())
        print("Test termin: " + _test_termin())
