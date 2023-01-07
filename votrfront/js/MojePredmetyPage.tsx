import React, { useContext } from "react";
import { CacheRequester, Loading } from "./ajax";
import {
  coursesStats,
  renderCredits,
  renderWeightedStudyAverage,
} from "./coursesStats";
import {
  classForSemester,
  humanizeTerminHodnotenia,
  humanizeTypVyucby,
  plural,
} from "./humanizeAISData";
import { PageLayout, PageTitle } from "./layout";
import { ScreenSize, underSM, underXS } from "./mediaQueries";
import { QueryContext, RelativeLink } from "./router";
import { Column, column, SortableTable, sortAs } from "./sorting";
import { Hodnotenie } from "./types";
import { ZapisnyListSelector } from "./ZapisnyListSelector";

export const MojePredmetyColumns: Column<Hodnotenie>[] = [
  column({
    label: "Semester",
    shortLabel: <abbr title="Semester">Sem.</abbr>,
    prop: "semester",
    preferDesc: true,
  }),
  column({
    label: "Názov predmetu",
    sortKey: (hodnotenie: Hodnotenie) => hodnotenie.nazov,
    display: (hodnotenie: Hodnotenie) => (
      <RelativeLink
        href={{
          modal: "detailPredmetu",
          modalPredmetKey: hodnotenie.predmet_key,
          modalAkademickyRok: hodnotenie.akademicky_rok,
        }}
      >
        {hodnotenie.nazov}
      </RelativeLink>
    ),
    expansionMark: true,
  }),
  column({ label: "Skratka predmetu", prop: "skratka", hide: underSM }),
  column({ label: "Kredit", prop: "kredit", sortKey: sortAs.number }),
  column({
    label: "Typ výučby",
    prop: "typ_vyucby",
    display: humanizeTypVyucby,
    hide: underXS,
  }),
  column({
    label: "Hodnotenie",
    projection: (hodnotenie: Hodnotenie) =>
      [hodnotenie.hodn_znamka, hodnotenie.hodn_znamka_popis]
        .filter(Boolean)
        .join(" - "),
  }),
  column({
    label: "Dátum hodnotenia",
    prop: "hodn_datum",
    sortKey: sortAs.date,
    hide: underSM,
  }),
  column({
    label: "Termín hodnotenia",
    prop: "hodn_termin",
    display: humanizeTerminHodnotenia,
    hide: underSM,
  }),
];

// Semester (descending), Nazov predmetu
const mojePredmetyDefaultOrder = "d0a1";

function MojePredmetyPageContent() {
  var query = useContext(QueryContext);
  var cache = new CacheRequester();
  var zapisnyListKey = query.zapisnyListKey!;

  var [hodnotenia, message] = cache.get("get_hodnotenia", zapisnyListKey) || [];

  if (!hodnotenia) {
    return <Loading requests={cache.missing} />;
  }

  var stats = coursesStats(hodnotenia);

  var footer = (size: ScreenSize) => (
    <tr>
      {size > ScreenSize.SM && <td />}
      <td colSpan={2}>
        Celkom {stats.spolu.count}{" "}
        {plural(stats.spolu.count, "predmet", "predmety", "predmetov")}
        {" ("}
        {stats.zima.count} v zime, {stats.leto.count} v lete)
      </td>
      <td>
        {renderCredits(stats.spolu)} ({renderCredits(stats.zima)}&nbsp;+&nbsp;
        {renderCredits(stats.leto)})
      </td>
      {size > ScreenSize.XS && <td />}
      <td>{renderWeightedStudyAverage(hodnotenia!)}</td>
      {size > ScreenSize.SM && <td />}
      {size > ScreenSize.SM && <td />}
    </tr>
  );

  return (
    <SortableTable
      items={hodnotenia}
      columns={MojePredmetyColumns}
      defaultOrder={mojePredmetyDefaultOrder}
      queryKey="predmetySort"
      expandedContentOffset={1}
      message={message}
      footer={footer}
      rowClassName={(hodnotenie) => classForSemester(hodnotenie.semester)}
    />
  );
}

export function makeMojePredmetyPage() {
  return (
    <PageLayout>
      <ZapisnyListSelector>
        <div className="header">
          <PageTitle>Moje predmety</PageTitle>
        </div>
        <MojePredmetyPageContent />
      </ZapisnyListSelector>
    </PageLayout>
  );
}
