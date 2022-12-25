import React, { useContext } from "react";
import { ZoznamPrihlasenychNaTerminColumns } from "./ZoznamPrihlasenychNaTermin";
import { CacheRequester, Loading } from "./ajax";
import { Modal } from "./layout";
import { QueryContext } from "./router";
import { sortAs, sortTable } from "./sorting";
import { Columns } from "./types";

export var DetailPredmetuUciteliaColumns: Columns = [
  ["Meno", "plne_meno", sortAs.personName],
  ["Typ", "typ"],
];
DetailPredmetuUciteliaColumns.defaultOrder = "a0";

export var DetailPredmetuStudentiColumns: Columns =
  ZoznamPrihlasenychNaTerminColumns.slice();
DetailPredmetuStudentiColumns.defaultOrder = "a0";

function getZapisaniStudenti(
  cache: CacheRequester,
  predmetKey: string,
  akademickyRok: string
) {
  return cache.get(
    "get_studenti_zapisani_na_predmet",
    predmetKey,
    akademickyRok
  );
}

function DetailPredmetuInformacnyList() {
  var query = useContext(QueryContext);
  var cache = new CacheRequester();
  var { modalAkademickyRok, modalPredmetKey } = query;

  var data = cache.get(
    "get_informacny_list",
    modalPredmetKey,
    modalAkademickyRok
  );

  if (!data) {
    return <Loading requests={cache.missing} />;
  }

  var url = "data:application/pdf;base64," + escape(data);
  return (
    <a href={url} download>
      Stiahnuť
    </a>
  );
}

function DetailPredmetuUcitelia() {
  var query = useContext(QueryContext);
  var cache = new CacheRequester();
  var { modalAkademickyRok, modalPredmetKey } = query;

  var data = getZapisaniStudenti(cache, modalPredmetKey, modalAkademickyRok);

  if (!data) {
    return <Loading requests={cache.missing} />;
  }

  var [studenti, predmet] = data;

  if (!predmet) {
    // https://github.com/microsoft/TypeScript/issues/21699
    return "Dáta pre predmet neboli nájdené." as unknown as JSX.Element;
  }

  var ucitelia = cache.get(
    "get_ucitelia_predmetu",
    modalPredmetKey,
    modalAkademickyRok,
    predmet.semester,
    predmet.fakulta
  );

  if (!ucitelia) {
    return <Loading requests={cache.missing} />;
  }

  var header;
  [ucitelia, header] = sortTable(
    ucitelia,
    DetailPredmetuUciteliaColumns,
    query,
    "modalUciteliaSort"
  );

  var message = ucitelia.length
    ? null
    : "Predmet nemá v AISe žiadnych učiteľov.";

  return (
    <table className="table table-condensed table-bordered table-striped table-hover">
      <thead>{header}</thead>
      <tbody>
        {ucitelia.map((ucitel, index) => (
          <tr key={index}>
            <td>{ucitel.plne_meno}</td>
            <td>{ucitel.typ}</td>
          </tr>
        ))}
      </tbody>
      {message && (
        <tfoot>
          <tr>
            <td colSpan={DetailPredmetuUciteliaColumns.length}>{message}</td>
          </tr>
        </tfoot>
      )}
    </table>
  );
}

function DetailPredmetuZapisaniStudenti() {
  var query = useContext(QueryContext);
  var cache = new CacheRequester();
  var { modalAkademickyRok, modalPredmetKey } = query;

  var data = getZapisaniStudenti(cache, modalPredmetKey, modalAkademickyRok);

  if (!data) {
    return <Loading requests={cache.missing} />;
  }

  var [studenti, predmet] = data;

  if (!predmet) {
    // https://github.com/microsoft/TypeScript/issues/21699
    return "Dáta pre predmet neboli nájdené." as unknown as JSX.Element;
  }

  var [studenti, header] = sortTable(
    studenti,
    DetailPredmetuStudentiColumns,
    query,
    "modalStudentiSort"
  );

  var message = studenti.length
    ? null
    : "Predmet nemá v AISe žiadnych zapísaných študentov.";

  return (
    <table className="table table-condensed table-bordered table-striped table-hover">
      <thead>{header}</thead>
      <tbody>
        {studenti.map((student, index) => (
          <tr key={index}>
            <td>{student.plne_meno}</td>
            <td>{student.sp_skratka}</td>
            <td>{student.rocnik}</td>
            <td>
              {student.email && (
                <a href={"mailto:" + student.email}>{student.email}</a>
              )}
            </td>
            <td>{student.datum_prihlasenia}</td>
          </tr>
        ))}
      </tbody>
      {message && (
        <tfoot>
          <tr>
            <td colSpan={DetailPredmetuStudentiColumns.length}>{message}</td>
          </tr>
        </tfoot>
      )}
    </table>
  );
}

function DetailPredmetuTitle() {
  var query = useContext(QueryContext);
  var cache = new CacheRequester();
  var { modalAkademickyRok, modalPredmetKey } = query;

  var data = getZapisaniStudenti(cache, modalPredmetKey, modalAkademickyRok);

  if (!data) {
    return <Loading requests={cache.missing} />;
  }

  var [studenti, predmet] = data;

  if (!predmet) {
    // https://github.com/microsoft/TypeScript/issues/21699
    return "Dáta nenájdené" as unknown as JSX.Element;
  }

  // https://github.com/microsoft/TypeScript/issues/21699
  return predmet.nazov as unknown as JSX.Element;
}

export function DetailPredmetuModal() {
  return (
    <Modal title={<DetailPredmetuTitle />}>
      <h4>Informačný list predmetu</h4>
      <DetailPredmetuInformacnyList />
      <h4>Učitelia</h4>
      <DetailPredmetuUcitelia />
      <h4>Zapísaní študenti</h4>
      <DetailPredmetuZapisaniStudenti />
    </Modal>
  );
}
