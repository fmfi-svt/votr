import React, { useContext } from "react";
import {
  CacheRequester,
  invalidateRequestCache,
  Loading,
  sendRpc,
} from "./ajax";
import { currentAcademicYear } from "./coursesStats";
import { PageLayout, PageTitle } from "./layout";
import { underSM, underXS } from "./mediaQueries";
import { QueryContext } from "./router";
import { column, SortableTable, sortAs } from "./sorting";
import { Studium, ZapisnyList } from "./types";

// TODO: Pridat kadejake sumarne informacie, aby to vyzeralo ako dashboard.
// TODO: Ked to raz bude rychle, pouzit to ako "home page" pri prazdnom action.
// TODO: Zvyraznit aktualne obdobia a pisat kolko casu zostava do dalsich.

const prehladStudiumColumns = [
  column({
    label: "Študijný program",
    projection: (item: Studium) => `${item.sp_popis} (${item.sp_skratka})`,
    expansionMark: true,
  }),
  column({
    label: "Rok štúdia",
    prop: "rok_studia",
    sortKey: sortAs.number,
    hide: underXS,
  }),
  column({
    label: "Dĺžka v semestroch",
    prop: "sp_dlzka",
    sortKey: sortAs.number,
    hide: underXS,
  }),
  column({ label: "Začiatok štúdia", prop: "zaciatok", sortKey: sortAs.date }),
  column({ label: "Koniec štúdia", prop: "koniec", sortKey: sortAs.date }),
  column({
    label: "Doplňujúce údaje",
    projection: (item: Studium) =>
      item.sp_doplnujuce_udaje.replace(/^\((.*)\)$/, "$1"),
    hide: underSM,
  }),
  column({
    label: "Zápisný list",
    sortKey: () => "",
    display: (studium: Studium) => (
      <PridatZapisnyListButton studium={studium} />
    ),
  }),
];

// Koniec studia
const prehladStudiumDefaultOrder = "d4";

const prehladZapisnyListColumns = [
  column({
    label: "Akademický rok",
    prop: "akademicky_rok",
    expansionMark: true,
  }),
  column({
    label: "Študijný program",
    projection: (item: ZapisnyList) => `${item.sp_popis} (${item.sp_skratka})`,
  }),
  column({ label: "Ročník", prop: "rocnik", sortKey: sortAs.number }),
  column({
    label: "Dátum zápisu",
    prop: "datum_zapisu",
    sortKey: sortAs.date,
    hide: underXS,
  }),
];

// Akademicky rok (descending), Datum zapisu
const prehladZapisnyListDefaultOrder = "d0d3";

function PrehladStudiaObdobie(props: {
  rpc: "get_semester_obdobie" | "get_skuskove_obdobie";
  semester: "Z" | "L";
  label: string;
}) {
  const cache = new CacheRequester();
  const result = cache.get(props.rpc, props.semester);
  return (
    <tr>
      <th>{props.label}</th>
      <td>
        {result ? (
          result.obdobie_od + " \u2013 " + result.obdobie_do
        ) : (
          <Loading requests={cache.missing} />
        )}
      </td>
    </tr>
  );
}

function PrehladStudiaObdobia() {
  const query = useContext(QueryContext);
  // Obdobia predsalen neukazujeme, lebo AIS ma vacsinou zle informacie
  // (skuskove je umelo predlzene kvoli moznosti zapisovat znamky, apod) a
  // nechceme byt matuci. Zapnut sa daju tymto schovanym query flagom.
  if (!query.reallyShowDates) {
    return null;
  }

  return (
    <table className="table table-narrow table-condensed table-bordered table-hover">
      <tbody>
        <PrehladStudiaObdobie
          label="Zimný semester"
          rpc="get_semester_obdobie"
          semester="Z"
        />
        <PrehladStudiaObdobie
          label="Zimné skúškové"
          rpc="get_skuskove_obdobie"
          semester="Z"
        />
        <PrehladStudiaObdobie
          label="Letný semester"
          rpc="get_semester_obdobie"
          semester="L"
        />
        <PrehladStudiaObdobie
          label="Letné skúškové"
          rpc="get_skuskove_obdobie"
          semester="L"
        />
      </tbody>
    </table>
  );
}

function PridatZapisnyListButton({ studium }: { studium: Studium }) {
  const rok = currentAcademicYear();

  if (studium.koniec !== "") {
    // Ak studium uz skoncilo, neukazeme nic.
    return null;
  }

  const cache = new CacheRequester();

  const zapisneListy = cache.get("get_zapisne_listy", studium.studium_key);

  if (!zapisneListy) {
    return <Loading requests={cache.missing} />;
  }

  // Ak uz mame zapisny list na tento rok, ukazeme disabled button.
  const uzExistuje = zapisneListy.some((zl) => zl.akademicky_rok === rok);

  function handleClick() {
    if (confirm(`Vytvoriť zápisný list pre akademický rok ${rok}?`)) {
      sendRpc(
        "create_zapisny_list",
        [studium.studium_key, rok, null],
        (message) => {
          if (message !== null) {
            alert(message);
          } else {
            invalidateRequestCache("get_zapisne_listy");
          }
        }
      );
    }
  }

  return (
    <button
      type="button"
      className="btn btn-xs btn-success"
      disabled={uzExistuje}
      onClick={uzExistuje ? undefined : handleClick}
    >
      Vytvoriť
    </button>
  );
}

function PrehladStudiaStudia() {
  const cache = new CacheRequester();

  const studia = cache.get("get_studia");

  if (!studia) {
    return <Loading requests={cache.missing} />;
  }

  const message = studia.length ? null : "V AISe nemáte žiadne štúdiá.";

  return (
    <SortableTable
      items={studia}
      columns={prehladStudiumColumns}
      defaultOrder={prehladStudiumDefaultOrder}
      queryKey="studiaSort"
      message={message}
    />
  );
}

function PrehladStudiaZapisneListy() {
  const cache = new CacheRequester();

  const studia = cache.get("get_studia");

  if (!studia) {
    return <Loading requests={cache.missing} />;
  }

  const zapisneListy: ZapisnyList[] = [];

  for (const studium of studia) {
    const mojeZapisneListy = cache.get(
      "get_zapisne_listy",
      studium.studium_key
    );
    if (mojeZapisneListy) zapisneListy.push(...mojeZapisneListy);
  }

  const showTable = !!zapisneListy.length || cache.loadedAll;

  const message = zapisneListy.length
    ? null
    : "V AISe nemáte žiadne zápisné listy.";

  return (
    <React.Fragment>
      {!cache.loadedAll && <Loading requests={cache.missing} />}
      {showTable && (
        <SortableTable
          items={zapisneListy}
          columns={prehladZapisnyListColumns}
          defaultOrder={prehladZapisnyListDefaultOrder}
          queryKey="zapisneListySort"
          message={message}
        />
      )}
    </React.Fragment>
  );
}

export function makePrehladStudiaPage() {
  return (
    <PageLayout>
      <div className="header">
        <PageTitle>Prehľad štúdia</PageTitle>
      </div>
      <PrehladStudiaObdobia />
      <h2>Zoznam štúdií</h2>
      <PrehladStudiaStudia />
      <h2>Zoznam zápisných listov</h2>
      <PrehladStudiaZapisneListy />
    </PageLayout>
  );
}
