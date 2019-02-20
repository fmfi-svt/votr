
import React from 'react';
import _ from 'lodash';
import { MojePredmetyColumns } from './MojePredmetyPage';
import { StudiumSelector } from './StudiumSelector';
import { CacheRequester, Loading } from './ajax';
import { coursesStats, renderWeightedStudyAverage } from './coursesStats';
import { classForSemester, humanizeNazovPriemeru, humanizeTerminHodnotenia, humanizeTypVyucby, plural } from './humanizeAISData';
import { PageLayout, PageTitle } from './layout';
import { Link, queryConsumer } from './router';
import { sortAs, SortableTable } from './sorting';


export var MojeHodnoteniaColumns = [
  {
    label:"Akademický rok",
    prop: 'akademicky_rok'
  }
].concat(MojePredmetyColumns);
MojeHodnoteniaColumns[1] = {
  ...MojeHodnoteniaColumns[1],
  hiddenClass: ["hidden-xs", "hidden-sm"]
};
MojeHodnoteniaColumns.defaultOrder = 'a0d1a2';


export var MojePriemeryColumns = [
  {
    label: "Dátum výpočtu priemeru",
    prop: "datum_vypoctu",
    process: sortAs.date,
    expansionMark: true
  },
  {
    label: "Názov priemeru",
    prop: "nazov",
    cell: (priemer, query) => humanizeNazovPriemeru(priemer.nazov)
  },
  { label: "Akademický rok", prop: "akademicky_rok" },
  {
    label: "Semester",
    prop: "semester",
    preferDesc: true
  },
  {
    label: "Získaný kredit",
    prop: "ziskany_kredit",
    process: sortAs.number,
    hiddenClass: ["hidden-xs", "hidden-sm"]
  },
  {
    label: "Celkový počet predmetov",
    prop: "predmetov",
    process: sortAs.number,
    hiddenClass: ["hidden-xs", "hidden-sm"]
  },
  {
    label: "Počet neabsolvovaných predmetov",
    prop: "neabsolvovanych",
    process: sortAs.number,
    hiddenClass: ["hidden-xs", "hidden-sm"]
  },
  {
    label: "Študijný priemer",
    prop: "studijny_priemer",
    process: sortAs.number,
    hiddenClass: ["hidden-xs"]
  },
  {
    label: "Vážený priemer",
    prop: "vazeny_priemer",
    process: sortAs.number,
    hiddenClass: ["hidden-xs"]
  }
];
MojePriemeryColumns.defaultOrder = "a0a2a1";


export function MojeHodnoteniaHodnoteniaTable() {
  return queryConsumer(query => {
    var cache = new CacheRequester();
    var {studiumKey} = query;
    var [hodnotenia, message] = cache.get('get_prehlad_kreditov', studiumKey) || [];

    if (!hodnotenia) {
      return <Loading requests={cache.missing} />;
    }

    var stats = coursesStats(hodnotenia);

    var footer = fullTable => (
      <tr>
        <td className={fullTable ? "" : "hidden-xs hidden-sm"} colSpan="2" />
        <td colSpan="2">
          Celkom {stats.spolu.count}{" "}
          {plural(stats.spolu.count, "predmet", "predmety", "predmetov")}
          {" ("}
          {stats.zima.count} v zime, {stats.leto.count} v lete)
        </td>
        <td>
          {stats.spolu.creditsCount} ({stats.zima.creditsCount}+
          {stats.leto.creditsCount})
        </td>
        <td className={fullTable ? "" : "hidden-xs"} />
        <td>{renderWeightedStudyAverage(hodnotenia)}</td>
        <td className={fullTable ? "" : "hidden-xs hidden-sm"} />
        <td className={fullTable ? "" : "hidden-xs hidden-sm"} />
      </tr>
    );

    return (
      <SortableTable
        items={hodnotenia}
        columns={MojeHodnoteniaColumns}
        queryKey="predmetySort"
        message={message}
        footer={footer}
        rowClassName={hodnotenie => classForSemester(hodnotenie.semester)}
      />
    );
  });
}

export function MojeHodnoteniaPriemeryTable() {
  return queryConsumer(query => {
    var cache = new CacheRequester();
    var {studiumKey} = query;

    var priemery, message;
    var zapisneListy = cache.get('get_zapisne_listy', studiumKey);

    if (zapisneListy && zapisneListy.length == 0) {
      priemery = [];
    } else if (zapisneListy) {
      var zapisnyListKey = _.maxBy(zapisneListy,
          (zapisnyList) => sortAs.date(zapisnyList.datum_zapisu)).zapisny_list_key;
      [priemery, message] = cache.get('get_priemery', zapisnyListKey) || [];
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
  });
}


export function MojeHodnoteniaPage() {
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
