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
import { ScreenSize } from "./mediaQueries";
import { MojePredmetyColumns } from "./MojePredmetyPage";
import { QueryContext } from "./router";
import { SortableTable, sortAs } from "./sorting";
import { StudiumSelector } from "./StudiumSelector";
import { Columns, Priemer } from "./types";

var MojeHodnoteniaColumns: Columns = [
  {
    label: "Akademický rok",
    prop: "akademicky_rok",
  },
].concat(MojePredmetyColumns);
MojeHodnoteniaColumns[1] = {
  ...MojeHodnoteniaColumns[1],
  hiddenClass: ["hidden-xs", "hidden-sm"],
};
MojeHodnoteniaColumns.defaultOrder = "a0d1a2";

var MojePriemeryColumns: Columns = [
  {
    label: "Dátum výpočtu priemeru",
    prop: "datum_vypoctu",
    sortKey: sortAs.date,
    expansionMark: true,
  },
  {
    label: "Názov priemeru",
    prop: "nazov",
    display: (priemer: Priemer) => humanizeNazovPriemeru(priemer.nazov),
  },
  { label: "Akademický rok", prop: "akademicky_rok" },
  {
    label: "Semester",
    shortLabel: <abbr title="Semester">Sem.</abbr>,
    prop: "semester",
    preferDesc: true,
  },
  {
    label: "Získaný kredit",
    prop: "ziskany_kredit",
    sortKey: sortAs.number,
    hiddenClass: ["hidden-xs", "hidden-sm"],
  },
  {
    label: "Celkový počet predmetov",
    prop: "predmetov",
    sortKey: sortAs.number,
    hiddenClass: ["hidden-xs", "hidden-sm"],
  },
  {
    label: "Počet neabsolvovaných predmetov",
    prop: "neabsolvovanych",
    sortKey: sortAs.number,
    hiddenClass: ["hidden-xs", "hidden-sm"],
  },
  {
    label: "Študijný priemer",
    prop: "studijny_priemer",
    sortKey: sortAs.number,
    hiddenClass: ["hidden-xs"],
  },
  {
    label: "Vážený priemer",
    prop: "vazeny_priemer",
    sortKey: sortAs.number,
    hiddenClass: ["hidden-xs"],
  },
];
MojePriemeryColumns.defaultOrder = "a0a2a1";

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
