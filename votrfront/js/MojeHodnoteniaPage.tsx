import _ from "lodash";
import React, { useContext } from "react";
import { CacheRequester, Loading } from "./ajax";
import {
  coursesStats,
  renderCredits,
  renderWeightedStudyAverage,
} from "./coursesStats";
import {
  classForSemester,
  humanizeNazovPriemeru,
  plural,
} from "./humanizeAISData";
import { PageLayout, PageTitle } from "./layout";
import { ScreenSize, underSM, underXS } from "./mediaQueries";
import { MojePredmetyColumns } from "./MojePredmetyPage";
import { QueryContext } from "./router";
import { Column, column, SortableTable, sortAs } from "./sorting";
import { StudiumSelector } from "./StudiumSelector";
import { Hodnotenie, Priemer } from "./types";

const [predmetSemesterColumn, ...predmetRemainingColumns] = MojePredmetyColumns;
const MojeHodnoteniaColumns: Column<Hodnotenie>[] = [
  column({ label: "Akademický rok", prop: "akademicky_rok" }),
  { ...predmetSemesterColumn!, hide: underSM },
  ...predmetRemainingColumns,
];

// Akademicky rok, Semester (descending), Nazov predmetu
const mojeHodnoteniaDefaultOrder = "a0d1a2";

const MojePriemeryColumns: Column<Priemer>[] = [
  column({
    label: "Dátum výpočtu priemeru",
    prop: "datum_vypoctu",
    sortKey: sortAs.date,
    expansionMark: true,
  }),
  column({
    label: "Názov priemeru",
    prop: "nazov",
    display: humanizeNazovPriemeru,
  }),
  column({ label: "Akademický rok", prop: "akademicky_rok" }),
  column({
    label: "Semester",
    shortLabel: <abbr title="Semester">Sem.</abbr>,
    prop: "semester",
    preferDesc: true,
  }),
  column({
    label: "Získaný kredit",
    prop: "ziskany_kredit",
    sortKey: sortAs.number,
    hide: underSM,
  }),
  column({
    label: "Celkový počet predmetov",
    prop: "predmetov",
    sortKey: sortAs.number,
    hide: underSM,
  }),
  column({
    label: "Počet neabsolvovaných predmetov",
    prop: "neabsolvovanych",
    sortKey: sortAs.number,
    hide: underSM,
  }),
  column({
    label: "Študijný priemer",
    prop: "studijny_priemer",
    sortKey: sortAs.number,
    hide: underXS,
  }),
  column({
    label: "Vážený priemer",
    prop: "vazeny_priemer",
    sortKey: sortAs.number,
    hide: underXS,
  }),
];

// Datum vypoctu priemeru, Akademicky rok, Nazov priemeru
const mojePriemeryDefaultOrder = "a0a2a1";

function MojeHodnoteniaHodnoteniaTable() {
  var query = useContext(QueryContext);
  var cache = new CacheRequester();
  var studiumKey = query.studiumKey!;

  var [hodnotenia, message] =
    cache.get("get_prehlad_kreditov", studiumKey) || [];

  if (!hodnotenia) {
    return <Loading requests={cache.missing} />;
  }

  var stats = coursesStats(hodnotenia);

  var footer = (size: ScreenSize) => (
    <tr>
      {size > ScreenSize.SM && <td colSpan={2} />}
      <td colSpan={2}>
        Celkom {stats.spolu.count}{" "}
        {plural(stats.spolu.count, "predmet", "predmety", "predmetov")}
      </td>
      <td>{renderCredits(stats.spolu)}</td>
      {size > ScreenSize.XS && <td />}
      <td>{renderWeightedStudyAverage(hodnotenia!)}</td>
      {size > ScreenSize.SM && <td />}
      {size > ScreenSize.SM && <td />}
    </tr>
  );

  return (
    <SortableTable
      items={hodnotenia}
      columns={MojeHodnoteniaColumns}
      defaultOrder={mojeHodnoteniaDefaultOrder}
      queryKey="predmetySort"
      message={message}
      footer={footer}
      rowClassName={(hodnotenie) => classForSemester(hodnotenie.semester)}
    />
  );
}

function MojeHodnoteniaPriemeryTable() {
  var query = useContext(QueryContext);
  var cache = new CacheRequester();
  var studiumKey = query.studiumKey!;

  var priemery: Priemer[] | undefined;
  var message: string | null | undefined;
  var zapisneListy = cache.get("get_zapisne_listy", studiumKey);

  if (zapisneListy && zapisneListy.length == 0) {
    priemery = [];
  } else if (zapisneListy) {
    var zapisnyListKey = _.maxBy(zapisneListy, (zapisnyList) =>
      sortAs.date(zapisnyList.datum_zapisu)
    )!.zapisny_list_key;
    [priemery, message] = cache.get("get_priemery", zapisnyListKey) || [];
  }

  if (!priemery) {
    return <Loading requests={cache.missing} />;
  }

  if (!message && !priemery.length) {
    message = "V AISe zatiaľ nie sú vypočítané žiadne priemery.";
  }

  return (
    <SortableTable
      items={priemery}
      columns={MojePriemeryColumns}
      defaultOrder={mojePriemeryDefaultOrder}
      queryKey="priemerySort"
      message={message}
    />
  );
}

export function makeMojeHodnoteniaPage() {
  return (
    <PageLayout>
      <StudiumSelector>
        <div className="header">
          <PageTitle>Moje hodnotenia</PageTitle>
        </div>
        <MojeHodnoteniaHodnoteniaTable />
        <h2>Moje priemery</h2>
        <MojeHodnoteniaPriemeryTable />
      </StudiumSelector>
    </PageLayout>
  );
}
