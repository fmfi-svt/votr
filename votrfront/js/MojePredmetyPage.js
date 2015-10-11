
import { ZapisnyListSelector } from './ZapisnyListSelector';
import { CacheRequester, Loading } from './ajax';
import { coursesStats, renderWeightedStudyAverage } from './coursesStats';
import { classForSemester, humanizeTerminHodnotenia, humanizeTypVyucby, plural } from './humanizeAISData';
import { PageLayout, PageTitle } from './layout';
import { Link } from './router';
import { sortAs, sortTable } from './sorting';


export var MojePredmetyColumns = [
  [<abbr title="Semester">Sem.</abbr>, 'semester', null, true],
  ["Názov predmetu", 'nazov'],
  ["Skratka predmetu", 'skratka'],
  ["Kredit", 'kredit', sortAs.number],
  ["Typ výučby", 'typ_vyucby'],
  ["Hodnotenie", 'hodn_znamka'],
  ["Dátum hodnotenia", 'hodn_datum', sortAs.date],
  ["Termín hodnotenia", 'hodn_termin']
];
MojePredmetyColumns.defaultOrder = 'd0a1';


export var MojePredmetyPageContent = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  renderContent() {
    var cache = new CacheRequester();
    var {zapisnyListKey} = this.props.query;
    var [hodnotenia, message] = cache.get('get_hodnotenia', zapisnyListKey) || [];

    if (!hodnotenia) {
      return <Loading requests={cache.missing} />;
    }

    var [hodnotenia, header] = sortTable(
      hodnotenia, MojePredmetyColumns, this.props.query, 'predmetySort');

    var stats = coursesStats(hodnotenia);

    return <table className="table table-condensed table-bordered table-striped table-hover">
      <thead>{header}</thead>
      <tbody>
        {hodnotenia.map((hodnotenie) =>
          <tr key={hodnotenie.hodn_key} className={classForSemester(hodnotenie.semester)}>
            <td>{hodnotenie.semester}</td>
            <td><Link href={{ ...this.props.query, modal: 'detailPredmetu', modalPredmetKey: hodnotenie.predmet_key, modalAkademickyRok: hodnotenie.akademicky_rok }}>
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
            <td colSpan="3">
              Celkom {stats.spolu.count} {plural(stats.spolu.count, "predmet", "predmety", "predmetov")}
              {" ("}{stats.zima.count} v zime, {stats.leto.count} v lete)
            </td>
            <td>{stats.spolu.creditsCount} ({stats.zima.creditsCount}+{stats.leto.creditsCount})</td>
            <td></td>
            <td>{renderWeightedStudyAverage(hodnotenia)}</td>
            <td></td>
            <td></td>
          </tr>
          {message && <tr><td colSpan={MojePredmetyColumns.length}>{message}</td></tr>}
      </tfoot>
    </table>;
  },

  render() {
    var {zapisnyListKey} = this.props.query;
    return <div>
      <div className="header">
        <PageTitle>Moje predmety</PageTitle>
      </div>
      {this.renderContent()}
    </div>;
  }
});


export var MojePredmetyPage = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  render() {
    return <PageLayout query={this.props.query}>
      <ZapisnyListSelector query={this.props.query} component={MojePredmetyPageContent} />
    </PageLayout>;
  }
});
