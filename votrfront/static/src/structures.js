
(function () {

// TODO: get rid of this.


Votr.convertStudium = function (array) {
  return {
    sp_skratka: array[0],
    sp_popis: array[1],
    sp_doplnujuce_udaje: array[2],
    zaciatok: array[3],
    koniec: array[4],
    sp_dlzka: array[5],
    sp_cislo: array[6],
    rok_studia: array[7],
    key: array[8]
  };
};


Votr.convertZapisnyList = function (array) {
  return {
    akademicky_rok: array[0],
    rocnik: array[1],
    sp_skratka: array[2],
    sp_popis: array[3],
    datum_zapisu: array[4],
    key: array[5]
  };
};


Votr.convertHodnotenie = function (array) {
  return {
    akademicky_rok: array[0],
    skratka: array[1],
    nazov: array[2],
    typ_vyucby: array[3],
    semester: array[4],
    kredit: array[5],
    hodn_znamka: array[6],
    hodn_termin: array[7],
    hodn_datum: array[8],
    hodn_znamka_popis: array[9]
  };
};


})();
