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
  akademickyRok: string,
) {
  return cache.get(
    "get_studenti_zapisani_na_predmet",
    predmetKey,
    akademickyRok,
  );
}

function DetailPredmetuInformacnyList() {
  const query = useContext(QueryContext);
  const cache = new CacheRequester();
  const { modalAkademickyRok, modalPredmetKey } = query;
  if (!modalAkademickyRok || !modalPredmetKey) return null;

  const data = cache.get(
    "get_informacny_list",
    modalPredmetKey,
    modalAkademickyRok,
  );

  if (!data) {
    return <Loading requests={cache.missing} />;
  }

  const url = "data:application/pdf;base64," + escape(data);
  return (
    <a href={url} download>
      Stiahnuť
    </a>
  );
}

function DetailPredmetuUcitelia() {
  const query = useContext(QueryContext);
  const cache = new CacheRequester();
  const { modalAkademickyRok, modalPredmetKey } = query;
  if (!modalAkademickyRok || !modalPredmetKey) return null;

  const data = getZapisaniStudenti(cache, modalPredmetKey, modalAkademickyRok);

  if (!data) {
    return <Loading requests={cache.missing} />;
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [studenti, predmet] = data;

  if (!predmet) {
    return "Dáta pre predmet neboli nájdené.";
  }

  const ucitelia = cache.get(
    "get_ucitelia_predmetu",
    modalPredmetKey,
    modalAkademickyRok,
    predmet.semester,
    predmet.fakulta,
  );

  if (!ucitelia) {
    return <Loading requests={cache.missing} />;
  }

  const message =
    ucitelia.length ? null : "Predmet nemá v AISe žiadnych učiteľov.";

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
  const query = useContext(QueryContext);
  const cache = new CacheRequester();
  const { modalAkademickyRok, modalPredmetKey } = query;
  if (!modalAkademickyRok || !modalPredmetKey) return null;

  const data = getZapisaniStudenti(cache, modalPredmetKey, modalAkademickyRok);

  if (!data) {
    return <Loading requests={cache.missing} />;
  }

  const [studenti, predmet] = data;

  if (!predmet) {
    return "Dáta pre predmet neboli nájdené.";
  }

  const message =
    studenti.length ? null : (
      "Predmet nemá v AISe žiadnych zapísaných študentov."
    );

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
  const query = useContext(QueryContext);
  const cache = new CacheRequester();
  const { modalAkademickyRok, modalPredmetKey } = query;
  if (!modalAkademickyRok || !modalPredmetKey) {
    return <em>Pokazená URL adresa!</em>;
  }

  const data = getZapisaniStudenti(cache, modalPredmetKey, modalAkademickyRok);

  if (!data) {
    return <Loading requests={cache.missing} />;
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [studenti, predmet] = data;

  if (!predmet) {
    return "Dáta nenájdené";
  }

  return predmet.nazov;
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
