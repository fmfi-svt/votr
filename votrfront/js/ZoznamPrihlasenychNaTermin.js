
import { CacheRequester, Loading } from './ajax';
import { Modal } from './layout';
import { sortAs, sortTable } from './sorting';


export var ZoznamPrihlasenychNaTerminColumns = [
  ["Meno", 'plne_meno', sortAs.personName],
  ["Študijný program", 'sp_skratka'],
  ["Ročník", 'rocnik', sortAs.number],
  ["E-mail", 'email'],
  ["Dátum prihlásenia", 'datum_prihlasenia', sortAs.date]
];


export var ZoznamPrihlasenychNaTerminModal = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  renderContent() {
    var cache = new CacheRequester();
    var {modalTerminKey} = this.props.query;

    if (!modalTerminKey) return null;
    var studenti = cache.get('get_prihlaseni_studenti', modalTerminKey);

    if (!studenti) {
      return <Loading requests={cache.missing} />;
    }

    var [studenti, header] = sortTable(
      studenti, ZoznamPrihlasenychNaTerminColumns,
      this.props.query, 'modalStudentiSort');

    var message = studenti.length ? null : "Na termín nie sú prihlásení žiadni študenti.";

    return <table className="table table-condensed table-bordered table-striped table-hover">
      <thead>{header}</thead>
      <tbody>
        {studenti.map((student, index) =>
          <tr key={index}>
            <td>{student.plne_meno}</td>
            <td>{student.sp_skratka}</td>
            <td>{student.rocnik}</td>
            <td><a href={"mailto:" + student.email}>{student.email}</a></td>
            <td>{student.datum_prihlasenia}</td>
          </tr>
        )}
      </tbody>
      {message && <tfoot><tr><td colSpan={ZoznamPrihlasenychNaTerminColumns.length}>{message}</td></tr></tfoot>}
    </table>;
  },

  render() {
    return <Modal title="Zoznam prihlásených na termín">
      {this.renderContent()}
    </Modal>;
  }
});
