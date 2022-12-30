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
import { ScreenSize } from "./mediaQueries";
import { QueryContext, RelativeLink } from "./router";
import { SortableTable, sortAs } from "./sorting";
import { Columns, Hodnotenie } from "./types";
import { ZapisnyListSelector } from "./ZapisnyListSelector";

export var MojePredmetyColumns: Columns = [
  {
    label: "Semester",
    shortLabel: <abbr title="Semester">Sem.</abbr>,
    prop: "semester",
    preferDesc: true,
  },
  {
    label: "Názov predmetu",
    prop: "nazov",
    cell: (hodnotenie: Hodnotenie) => (
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
  },
  {
    label: "Skratka predmetu",
    prop: "skratka",
    hiddenClass: ["hidden-xs", "hidden-sm"],
  },
  { label: "Kredit", prop: "kredit", process: sortAs.number },
  {
    label: "Typ výučby",
    prop: "typ_vyucby",
    cell: (hodnotenie: Hodnotenie) => humanizeTypVyucby(hodnotenie.typ_vyucby),
    hiddenClass: ["hidden-xs"],
  },
  {
    label: "Hodnotenie",
    prop: "hodn_znamka",
    cell: (hodnotenie: Hodnotenie) =>
      (hodnotenie.hodn_znamka ? hodnotenie.hodn_znamka + " - " : "") +
      hodnotenie.hodn_znamka_popis,
  },
  {
    label: "Dátum hodnotenia",
    prop: "hodn_datum",
    process: sortAs.date,
    hiddenClass: ["hidden-xs", "hidden-sm"],
  },
  {
    label: "Termín hodnotenia",
    prop: "hodn_termin",
    cell: (hodnotenie: Hodnotenie) =>
      humanizeTerminHodnotenia(hodnotenie.hodn_termin),
    hiddenClass: ["hidden-xs", "hidden-sm"],
  },
];
MojePredmetyColumns.defaultOrder = "d0a1";

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
