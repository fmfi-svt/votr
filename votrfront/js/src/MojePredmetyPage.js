import React, { Component } from 'react';
import PropTypes from 'prop-types';

import { ZapisnyListSelector } from './ZapisnyListSelector';
import { CacheRequester, Loading } from './ajax';
import { coursesStats, renderWeightedStudyAverage } from './coursesStats';
import { classForSemester, humanizeTerminHodnotenia, humanizeTypVyucby, plural } from './humanizeAISData';
import { PageLayout, PageTitle } from './layout';
import { Link } from './router';
import { sortAs, sortTable } from './sorting';


export const MojePredmetyColumns = [
  [<abbr title="Semester">Sem.</abbr>, 'semester', null, true],
  ['Názov predmetu', 'nazov'],
  ['Skratka predmetu', 'skratka'],
  ['Kredit', 'kredit', sortAs.number],
  ['Typ výučby', 'typ_vyucby'],
  ['Hodnotenie', 'hodn_znamka'],
  ['Dátum hodnotenia', 'hodn_datum', sortAs.date],
  ['Termín hodnotenia', 'hodn_termin'],
];
MojePredmetyColumns.defaultOrder = 'd0a1';

export class MojePredmetyPageContent extends Component {

  renderContent = () => {
    const cache = new CacheRequester();
    const { zapisnyListKey } = this.props.query;
    let [hodnotenia, message] = cache.get('get_hodnotenia', zapisnyListKey) || [];

    if (!hodnotenia) {
      return <Loading requests={cache.missing} />;
    }

    let header;
    [hodnotenia, header] = sortTable(
      hodnotenia, MojePredmetyColumns, this.props.query, 'predmetySort');

    const stats = coursesStats(hodnotenia);

    return (
      <table className="table table-condensed table-bordered table-striped table-hover">
        <thead>{header}</thead>
        <tbody>
          {hodnotenia.map((hodnotenie) => (
            <tr key={hodnotenie.hodn_key} className={classForSemester(hodnotenie.semester)}>
              <td>{hodnotenie.semester}</td>
              <td>
                <Link
                  href={{
                    ...this.props.query,
                    modal: 'detailPredmetu',
                    modalPredmetKey: hodnotenie.predmet_key,
                    modalAkademickyRok: hodnotenie.akademicky_rok,
                  }}
                >
                  {hodnotenie.nazov}
                </Link>
              </td>
              <td>{hodnotenie.skratka}</td>
              <td>{hodnotenie.kredit}</td>
              <td>{humanizeTypVyucby(hodnotenie.typ_vyucby)}</td>
              <td>
                {hodnotenie.hodn_znamka}
                {hodnotenie.hodn_znamka ? ' - ' : null}
                {hodnotenie.hodn_znamka_popis}
              </td>
              <td>{hodnotenie.hodn_datum}</td>
              <td>{humanizeTerminHodnotenia(hodnotenie.hodn_termin)}</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <td colSpan="3">
              Celkom {stats.spolu.count} {plural(stats.spolu.count, 'predmet', 'predmety', 'predmetov')}
              {' ('}{stats.zima.count} v zime, {stats.leto.count} v lete)
            </td>
            <td>{stats.spolu.creditsCount} ({stats.zima.creditsCount}+{stats.leto.creditsCount})</td>
            <td />
            <td>{renderWeightedStudyAverage(hodnotenia)}</td>
            <td />
            <td />
          </tr>
          {message && <tr><td colSpan={MojePredmetyColumns.length}>{message}</td></tr>}
        </tfoot>
      </table>
    );
  }

  render() {
    const { zapisnyListKey } = this.props.query;
    return (
      <div>
        <div className="header">
          <PageTitle>Moje predmety</PageTitle>
        </div>
        {this.renderContent()}
      </div>
    );
  }
}

MojePredmetyPageContent.propTypes = {
  query: PropTypes.object.isRequired,
};

export class MojePredmetyPage extends Component {

  render() {
    return (
      <PageLayout query={this.props.query}>
        <ZapisnyListSelector query={this.props.query} component={MojePredmetyPageContent} />
      </PageLayout>
    );
  }
}

MojePredmetyPage.propTypes = {
  query: PropTypes.object.isRequired,
};
