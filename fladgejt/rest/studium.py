
from aisikl.app import Application
from fladgejt.structures import Studium, ZapisnyList, Hodnotenie, Predmet
import json


class RestStudiumMixin:

    def get_studia(self):

        response = self.context.request_json('/studium/')

        studia = json.loads(response)['response']

        result = [Studium(sp_skratka=studium['studijnyProgramSkratka'],
                          sp_popis=studium['studijnyProgramPopis'],
                          sp_doplnujuce_udaje=studium['studijnyProgramDoplnujuceUdaje'],
                          zaciatok=studium['zaciatokStudia'],
                          koniec=studium['koniecStudia'],
                          sp_dlzka=studium['studijnyProgramDlzka'],
                          sp_cislo=studium['studijnyProgramIdProgramCRS'],
                          rok_studia=studium['rokStudia'])
                  for studium in studia]
        return result

    def get_zapisne_listy(self, studijny_program):

        sp_id = self._get_studium_id(studijny_program)

        response = self.context.request_json('/studium/' + str(sp_id) + '/zapisneListy/')

        zapisneListy = json.loads(response)['response']

        result = [ZapisnyList(akademicky_rok=zapisnyList['popisAkadRok'],
                          rocnik=zapisnyList['rokRocnik'],
                          sp_skratka=zapisnyList['studProgramSkratka'],
                          sp_popis=zapisnyList['studProgramPopis'],
                          datum_zapisu=zapisnyList['datumZapisu'])
                  for zapisnyList in zapisneListy]
                  
        return result

    def get_prehlad_kreditov(self, studijny_program):

        sp_id = self._get_studium_id(studijny_program)

        response = self.context.request_json('/studium/' + str(sp_id) + '/zapisneListy/')

        zapisneListy = json.loads(response)['response']

        result = []

        for zapisnyList in zapisneListy:
          response = self.context.request_json('/zapisnyList/' + str(zapisnyList['id']) + '/predmety/')

          predmety = json.loads(response)['response']

          for predmet in predmety:
            result.append(Predmet(skratka=predmet['skratka'],
                          nazov=predmet['nazov'],
                          typ_vyucby=predmet['kodTypVyucby'],
                          semester=predmet['semester'],
                          kredit=predmet['kredit']))
                    

        return result

    def _get_studium_id(self, studijny_program):
        response = self.context.request_json('/studium/')

        studia = json.loads(response)['response']

        sp_id = None;

        for studium in studia:
          if studium['studijnyProgramSkratka'] == studijny_program.sp_skratka and studium['zaciatokStudia'] == studijny_program.zaciatok:
            sp_id = studium['id']
            break

        return sp_id