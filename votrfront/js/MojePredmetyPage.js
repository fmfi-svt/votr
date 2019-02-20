
import React from 'react';
import { ZapisnyListSelector } from './ZapisnyListSelector';
import { CacheRequester, Loading } from './ajax';
import { coursesStats, renderWeightedStudyAverage } from './coursesStats';
import { classForSemester, humanizeTerminHodnotenia, humanizeTypVyucby, plural } from './humanizeAISData';
import { PageLayout, PageTitle } from './layout';
import { Link, queryConsumer } from './router';
import { sortAs, SortableTable } from './sorting';

export var MojePredmetyColumns = [
  {
    label: "Sem.",
    shortLabel: <abbr title="Semester">Sem.</abbr>,
    prop: "semester",
    preferDesc: true
  },
  {
    label: "Názov predmetu",
    prop: "nazov",
    cell: (hodnotenie, query) => (
      <Link
        href={{
          ...query,
          modal: "detailPredmetu",
          modalPredmetKey: hodnotenie.predmet_key,
          modalAkademickyRok: hodnotenie.akademicky_rok
        }}
      >
        {hodnotenie.nazov}
      </Link>
    ),
    expansionMark: true
  },
  {
    label: "Skratka predmetu",
    prop: "skratka",
    hiddenClass: ["hidden-xs", "hidden-sm"]
  },
  { label: "Kredit", prop: "kredit", process: sortAs.number },
  {
    label: "Typ výučby",
    prop: "typ_vyucby",
    cell: (hodnotenie, query) => humanizeTypVyucby(hodnotenie.typ_vyucby),
    hiddenClass: ["hidden-xs"]
  },
  {
    label: "Hodnotenie",
    prop: "hodn_znamka",
    cell: hodnotenie => `${hodnotenie.hodn_znamka}${
      hodnotenie.hodn_znamka ? " - " : null}${
        hodnotenie.hodn_znamka_popis}`
  },
  {
    label: "Dátum hodnotenia",
    prop: "hodn_datum",
    process: sortAs.date,
    hiddenClass: ["hidden-xs", "hidden-sm"]
  },
  {
    label: "Termín hodnotenia",
    prop: "hodn_termin",
    cell: hodnotenie => humanizeTerminHodnotenia(hodnotenie.hodn_termin),
    hiddenClass: ["hidden-xs", "hidden-sm"]
  }
];
MojePredmetyColumns.defaultOrder = 'd0a1';


export function MojePredmetyPageContent() {
  return queryConsumer(query => {
    var cache = new CacheRequester();
    var {zapisnyListKey} = query;
    var [hodnotenia, message] = cache.get('get_hodnotenia', zapisnyListKey) || [];

    if (!hodnotenia) {
      return <Loading requests={cache.missing} />;
    }

    var stats = coursesStats(hodnotenia);

    var footer = fullTable => (
      <tr>
        <td className={fullTable ? "" : "hidden-xs hidden-sm"} />
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

    return <SortableTable
      items={hodnotenia}
      columns={MojePredmetyColumns}
      queryKey="predmetySort"
      expandedContentOffset={1}
      message={message}
      footer={footer}
      rowClassName={hodnotenie => classForSemester(hodnotenie.semester)}
    />;
  });
}


export function MojePredmetyPage() {
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
