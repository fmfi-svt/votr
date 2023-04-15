import React, { useContext } from "react";
import { CacheRequester, Loading } from "./ajax";
import { Modal } from "./layout";
import { QueryContext } from "./router";
import { column, SortableTable, sortAs } from "./sorting";
import { prihlasenyStudentColumns } from "./ZoznamPrihlasenychNaTermin";

const regUcitelPredmetuColumns = [
  column({ label: "Meno", prop: "plne_meno", sortKey: sortAs.personName }),
  column({ label: "Typ", prop: "typ" }),
];

// Meno
const detailPredmetuUciteliaDefaultOrder = "a0";

// Meno
const detailPredmetuStudentiDefaultOrder = "a0";

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
  if (!modalAkademickyRok || !modalPredmetKey) return null;

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
  if (!modalAkademickyRok || !modalPredmetKey) return null;

  var data = getZapisaniStudenti(cache, modalPredmetKey, modalAkademickyRok);

  if (!data) {
    return <Loading requests={cache.missing} />;
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
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

  var message = ucitelia.length
    ? null
    : "Predmet nemá v AISe žiadnych učiteľov.";

  return (
    <SortableTable
      items={ucitelia}
      columns={regUcitelPredmetuColumns}
      defaultOrder={detailPredmetuUciteliaDefaultOrder}
      queryKey="modalUciteliaSort"
      message={message}
    />
  );
}

function DetailPredmetuZapisaniStudenti() {
  var query = useContext(QueryContext);
  var cache = new CacheRequester();
  var { modalAkademickyRok, modalPredmetKey } = query;
  if (!modalAkademickyRok || !modalPredmetKey) return null;

  var data = getZapisaniStudenti(cache, modalPredmetKey, modalAkademickyRok);

  if (!data) {
    return <Loading requests={cache.missing} />;
  }

  var [studenti, predmet] = data;

  if (!predmet) {
    // https://github.com/microsoft/TypeScript/issues/21699
    return "Dáta pre predmet neboli nájdené." as unknown as JSX.Element;
  }

  var message = studenti.length
    ? null
    : "Predmet nemá v AISe žiadnych zapísaných študentov.";

  return (
    <SortableTable
      items={studenti}
      columns={prihlasenyStudentColumns}
      defaultOrder={detailPredmetuStudentiDefaultOrder}
      queryKey="modalStudentiSort"
      message={message}
    />
  );
}

function DetailPredmetuTitle() {
  var query = useContext(QueryContext);
  var cache = new CacheRequester();
  var { modalAkademickyRok, modalPredmetKey } = query;
  if (!modalAkademickyRok || !modalPredmetKey) {
    return <em>Pokazená URL adresa!</em>;
  }

  var data = getZapisaniStudenti(cache, modalPredmetKey, modalAkademickyRok);

  if (!data) {
    return <Loading requests={cache.missing} />;
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
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
