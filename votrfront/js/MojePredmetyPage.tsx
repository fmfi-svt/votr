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
import { Column, column, FooterCell, SortableTable, sortAs } from "./sorting";
import { Hodnotenie } from "./types";
import { ZapisnyListSelector } from "./ZapisnyListSelector";

interface FooterData {
  pocet: FooterCell;
  kredity: FooterCell;
  priemer: FooterCell;
}

export interface MojePredmetyColumn extends Column<Hodnotenie> {
  footer(f: FooterData, size: ScreenSize): FooterCell;
}

export const MojePredmetyColumns: MojePredmetyColumn[] = [
  column({
    label: "Semester",
    shortLabel: <abbr title="Semester">Sem.</abbr>,
    prop: "semester",
    preferDesc: true,
    footer: (f: FooterData, size: ScreenSize) =>
      size <= ScreenSize.SM ? undefined : null,
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
    footer: (f: FooterData) => f.pocet,
  }),
  column({
    label: "Skratka predmetu",
    prop: "skratka",
    hide: underSM,
    footer: () => undefined,
  }),
  column({
    label: "Kredit",
    prop: "kredit",
    sortKey: sortAs.number,
    footer: (f: FooterData) => f.kredity,
  }),
  column({
    label: "Typ výučby",
    prop: "typ_vyucby",
    display: humanizeTypVyucby,
    hide: underXS,
    footer: () => null,
  }),
  column({
    label: "Hodnotenie",
    projection: (hodnotenie: Hodnotenie) =>
      [hodnotenie.hodn_znamka, hodnotenie.hodn_znamka_popis]
        .filter(Boolean)
        .join(" - "),
    footer: (f: FooterData) => f.priemer,
  }),
  column({
    label: "Dátum hodnotenia",
    prop: "hodn_datum",
    sortKey: sortAs.date,
    hide: underSM,
    footer: () => null,
  }),
  column({
    label: "Termín hodnotenia",
    prop: "hodn_termin",
    display: humanizeTerminHodnotenia,
    hide: underSM,
    footer: () => null,
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
  var footerData: FooterData = {
    pocet:
      `Celkom ${stats.spolu.count} ` +
      plural(stats.spolu.count, "predmet", "predmety", "predmetov") +
      ` (${stats.zima.count} v zime, ${stats.leto.count} v lete)`,
    kredity: (
      <React.Fragment>
        {renderCredits(stats.spolu)}
        {" ("}
        {renderCredits(stats.zima)}
        &nbsp;+&nbsp;
        {renderCredits(stats.leto)}
        {")"}
      </React.Fragment>
    ),
    priemer: renderWeightedStudyAverage(hodnotenia),
  };

  return (
    <SortableTable
      items={hodnotenia}
      columns={MojePredmetyColumns}
      defaultOrder={mojePredmetyDefaultOrder}
      queryKey="predmetySort"
      expandedContentOffset={1}
      footers={(size) => [
        MojePredmetyColumns.map((col) => col.footer(footerData, size)),
        [message],
      ]}
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
