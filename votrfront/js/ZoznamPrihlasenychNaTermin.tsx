import React, { useContext } from "react";
import { CacheRequester, Loading } from "./ajax";
import { Modal } from "./layout";
import { underSM, underXS } from "./mediaQueries";
import { QueryContext } from "./router";
import { column, SortableTable, sortAs } from "./sorting";

export const prihlasenyStudentColumns = [
  column({
    label: "Meno",
    prop: "plne_meno",
    sortKey: sortAs.personName,
    expansionMark: true,
  }),
  column({
    label: "Študijný program",
    shortLabel: <abbr title="Študijný program">ŠP</abbr>,
    prop: "sp_skratka",
  }),
  column({ label: "Ročník", prop: "rocnik", sortKey: sortAs.number }),
  column({
    label: "E-mail",
    prop: "email",
    display: (email: string) =>
      !!email && <a href={"mailto:" + email}>{email}</a>,
    hide: underXS,
  }),
  column({
    label: "Dátum prihlásenia",
    prop: "datum_prihlasenia",
    sortKey: sortAs.date,
    hide: underSM,
  }),
];

function ZoznamPrihlasenychNaTerminModalContent() {
  var query = useContext(QueryContext);
  var cache = new CacheRequester();
  var { modalTerminKey } = query;

  if (!modalTerminKey) return null;
  var studenti = cache.get("get_prihlaseni_studenti", modalTerminKey);

  if (!studenti) {
    return <Loading requests={cache.missing} />;
  }

  var message = studenti.length
    ? null
    : "Na termín nie sú prihlásení žiadni študenti.";

  return (
    <SortableTable
      items={studenti}
      columns={prihlasenyStudentColumns}
      queryKey="modalStudentiSort"
      message={message}
    />
  );
}

export function ZoznamPrihlasenychNaTerminModal() {
  return (
    <Modal title="Zoznam prihlásených na termín">
      <ZoznamPrihlasenychNaTerminModalContent />
    </Modal>
  );
}
