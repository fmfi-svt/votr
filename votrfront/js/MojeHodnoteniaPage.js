
import React from 'react';
import _ from 'lodash';
import { MojePredmetyColumnsArr } from './MojePredmetyPage';
import { StudiumSelector } from './StudiumSelector';
import { CacheRequester, Loading } from './ajax';
import { coursesStats, renderWeightedStudyAverage } from './coursesStats';
import { classForSemester, humanizeNazovPriemeru, humanizeTerminHodnotenia, humanizeTypVyucby, plural } from './humanizeAISData';
import { PageLayout, PageTitle } from './layout';
import { Link, queryConsumer } from './router';
import { sortAs, sortTable } from './sorting';


export var MojeHodnoteniaColumns = [
  ["Akademický rok", 'akademicky_rok']
].concat(MojePredmetyColumnsArr);
MojeHodnoteniaColumns.defaultOrder = 'a0d1a2';


export var MojePriemeryColumns = [
  ["Dátum výpočtu priemeru", 'datum_vypoctu', sortAs.date],
  ["Názov priemeru", 'nazov'],
  ["Akademický rok", 'akademicky_rok'],
  ["Semester", 'semester', null, true],
  ["Získaný kredit", 'ziskany_kredit', sortAs.number],
  ["Celkový počet predmetov", 'predmetov', sortAs.number],
  ["Počet neabsolvovaných predmetov", 'neabsolvovanych', sortAs.number],
  ["Študijný priemer", 'studijny_priemer', sortAs.number],
  ["Vážený priemer", 'vazeny_priemer', sortAs.number]
];
MojePriemeryColumns.defaultOrder = 'a0a2a1';


export function MojeHodnoteniaHodnoteniaTable() {
  return queryConsumer(query => {
    var cache = new CacheRequester();
    var {studiumKey} = query;
    var [hodnotenia, message] = cache.get('get_prehlad_kreditov', studiumKey) || [];

    if (!hodnotenia) {
      return <Loading requests={cache.missing} />;
    }

    var [hodnotenia, header] = sortTable(
      hodnotenia, MojeHodnoteniaColumns, query, 'predmetySort');

    var stats = coursesStats(hodnotenia);

    return <table className="table table-condensed table-bordered table-striped table-hover">
      <thead>{header}</thead>
      <tbody>
        {hodnotenia.map((hodnotenie) =>
          <tr key={hodnotenie.hodn_key} className={classForSemester(hodnotenie.semester)}>
            <td>{hodnotenie.akademicky_rok}</td>
            <td>{hodnotenie.semester}</td>
            <td><Link href={{ ...query, modal: 'detailPredmetu', modalPredmetKey: hodnotenie.predmet_key, modalAkademickyRok: hodnotenie.akademicky_rok }}>
              {hodnotenie.nazov}
            </Link></td>
            <td>{hodnotenie.skratka}</td>
            <td>{hodnotenie.kredit}</td>
            <td>{humanizeTypVyucby(hodnotenie.typ_vyucby)}</td>
            <td>
              {hodnotenie.hodn_znamka}
              {hodnotenie.hodn_znamka ? " - " : null}
              {hodnotenie.hodn_znamka_popis}
            </td>
            <td>{hodnotenie.hodn_datum}</td>
            <td>{humanizeTerminHodnotenia(hodnotenie.hodn_termin)}</td>
          </tr>
        )}
      </tbody>
      <tfoot>
          <tr>
            <td colSpan="4">Celkom {stats.spolu.count} {plural(stats.spolu.count, "predmet", "predmety", "predmetov")}</td>
            <td>{stats.spolu.creditsCount}</td>
            <td></td>
            <td>{renderWeightedStudyAverage(hodnotenia)}</td>
            <td></td>
            <td></td>
          </tr>
          {message && <tr><td colSpan={MojeHodnoteniaColumns.length}>{message}</td></tr>}
      </tfoot>
    </table>;
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

    var [priemery, header] = sortTable(
      priemery, MojePriemeryColumns, query, 'priemerySort');

    if (!message && !priemery.length) {
      message = "V AISe zatiaľ nie sú vypočítané žiadne priemery.";
    }

    return <table className="table table-condensed table-bordered table-striped table-hover">
      <thead>{header}</thead>
      <tbody>
        {priemery.map((priemer, index) =>
          <tr key={index}>
            <td>{priemer.datum_vypoctu}</td>
            <td>{humanizeNazovPriemeru(priemer.nazov)}</td>
            <td>{priemer.akademicky_rok}</td>
            <td>{priemer.semester}</td>
            <td>{priemer.ziskany_kredit}</td>
            <td>{priemer.predmetov}</td>
            <td>{priemer.neabsolvovanych}</td>
            <td>{priemer.studijny_priemer}</td>
            <td>{priemer.vazeny_priemer}</td>
          </tr>
        )}
      </tbody>
      {message && <tfoot><tr><td colSpan={MojePriemeryColumns.length}>{message}</td></tr></tfoot>}
    </table>;
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
