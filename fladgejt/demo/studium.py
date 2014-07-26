
from aisikl.app import Application
from fladgejt.structures import Studium, ZapisnyList, Hodnotenie, Predmet
from fladgejt.demo.db import studia



class DemoStudiumMixin:
    def get_studia(self):
        return studia.get_studia()

    def get_zapisne_listy(self, studijny_program_skratka, zaciatok_studia):
        sp_id = self.get_studium_id(studijny_program_skratka, zaciatok_studia)

        zapisneListy = self.context.request_json(
            "/studium/{}/zapisneListy/".format(sp_id))

        result = [ZapisnyList(akademicky_rok=zapisnyList['popisAkadRok'],
                              rocnik=zapisnyList['rokRocnik'],
                              sp_skratka=zapisnyList['studProgramSkratka'],
                              sp_popis=zapisnyList['studProgramPopis'],
                              datum_zapisu=zapisnyList['datumZapisu'])
                  for zapisnyList in zapisneListy]

        return result

    # def get_prehlad_kreditov(self, studijny_program):
    #     sp_id = self.get_studium_id(studijny_program)

    #     zapisneListy = self.context.request_json(
    #         "/studium/{}/zapisneListy/".format(sp_id))

    #     result = []

    #     for zapisnyList in zapisneListy:
    #         predmety = self.context.request_json(
    #             "/zapisnyList/{}/predmety/".format(zapisnyList['id']))

    #         for predmet in predmety:
    #             result.append(Predmet(skratka=predmet['skratka'],
    #                                   nazov=predmet['nazov'],
    #                                   typ_vyucby=predmet['kodTypVyucby'],
    #                                   semester=predmet['semester'],
    #                                   kredit=predmet['kredit']))

    #     return result

    def get_studium_id(self, studijny_program_skratka, zaciatok_studia):
        studia = self.context.request_json('/studium/')

        for studium in studia:
            if studium['studijnyProgramSkratka'] == studijny_program_skratka and studium[
                    'zaciatokStudia'] == zaciatok_studia:
                return studium['id']

        raise RESTNotFoundError("Studium does not exists.")

    def get_zapisny_list_id(
            self,
            studijny_program_skratka,
            zaciatok_studia,
            akademicky_rok):
        sp_id = self.get_studium_id(studijny_program_skratka, zaciatok_studia)

        zapisneListy = self.context.request_json(
            "/studium/{}/zapisneListy/".format(sp_id))

        for zapisnyList in zapisneListy:
            if zapisnyList['popisAkadRok'] == akademicky_rok:
                return zapisnyList['id']

        raise RESTNotFoundError("Zapisny list does not exists.")

    def get_predmet_id(
            self,
            studijny_program_skratka,
            zaciatok_studia,
            akademicky_rok,
            skratka_predmetu):
        zl_id = self.get_zapisny_list_id(
            studijny_program_skratka,
            zaciatok_studia,
            akademicky_rok)

        predmety = self.context.request_json(
            "/zapisnyList/{}/predmety/".format(zl_id))

        for predmet in predmety:
            if predmet['skratka'] == skratka_predmetu:
                return predmet['id']

        raise RESTNotFoundError("Predmet does not exists.")
