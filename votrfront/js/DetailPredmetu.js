
import { ZoznamPrihlasenychNaTerminColumns } from './ZoznamPrihlasenychNaTermin';
import { CacheRequester, Loading } from './ajax';
import { Modal } from './layout';
import { sortAs, sortTable } from './sorting';


export var DetailPredmetuUciteliaColumns = [
  ["Meno", 'plne_meno', sortAs.personName],
  ["Typ", 'typ']
];
DetailPredmetuUciteliaColumns.defaultOrder = 'a0';

export var DetailPredmetuStudentiColumns = ZoznamPrihlasenychNaTerminColumns.slice();
DetailPredmetuStudentiColumns.defaultOrder = 'a0';

export var DetailPredmetuModal = createReactClass({
  getZapisaniStudenti(cache, predmetKey, akademickyRok){
    return cache.get('get_studenti_zapisani_na_predmet', predmetKey, akademickyRok);
  },

  renderInformacnyListPredmetu() {
    var cache = new CacheRequester();
    var {modalAkademickyRok, modalPredmetKey} = this.props.query;

    var data = cache.get('get_informacny_list', modalPredmetKey, modalAkademickyRok);

    if (!data) {
      return <Loading requests={cache.missing} />;
    }

    var url = "data:application/pdf;base64," + escape(data);
    return <a href={url} download>Stiahnuť</a>;
  },

  renderUcitelia() {
    var cache = new CacheRequester();
    var {modalAkademickyRok, modalPredmetKey} = this.props.query;

    var data = this.getZapisaniStudenti(cache, modalPredmetKey, modalAkademickyRok);

    if (!data) {
      return <Loading requests={cache.missing} />;
    }

    var [studenti, predmet] = data;

    if (!predmet) {
      return "Dáta pre predmet neboli nájdené.";
    }

    var ucitelia = cache.get('get_ucitelia_predmetu', modalPredmetKey, modalAkademickyRok, predmet.semester, predmet.fakulta);

    if (!ucitelia) {
      return <Loading requests={cache.missing} />;
    }

    var [ucitelia, header] = sortTable(
      ucitelia, DetailPredmetuUciteliaColumns, this.props.query, 'modalUciteliaSort');

    var message = ucitelia.length ? null : "Predmet nemá v AISe žiadnych učiteľov.";

    return <table className="table table-condensed table-bordered table-striped table-hover">
      <thead>{header}</thead>
      <tbody>
        {ucitelia.map((ucitel, index) =>
          <tr key={index}>
            <td>{ucitel.plne_meno}</td>
            <td>{ucitel.typ}</td>
          </tr>
        )}
      </tbody>
      {message && <tfoot><tr><td colSpan={DetailPredmetuUciteliaColumns.length}>{message}</td></tr></tfoot>}
    </table>;
  },

  renderZapisaniStudenti() {
    var cache = new CacheRequester();
    var {modalAkademickyRok, modalPredmetKey} = this.props.query;

    var data = this.getZapisaniStudenti(cache, modalPredmetKey, modalAkademickyRok);

    if (!data) {
      return <Loading requests={cache.missing} />;
    }

    var [studenti, predmet] = data;

    if (!predmet) {
      return "Dáta pre predmet neboli nájdené.";
    }

    var [studenti, header] = sortTable(
      studenti, DetailPredmetuStudentiColumns, this.props.query, 'modalStudentiSort');

    var message = studenti.length ? null : "Predmet nemá v AISe žiadnych zapísaných študentov.";

    return <table className="table table-condensed table-bordered table-striped table-hover">
      <thead>{header}</thead>
      <tbody>
        {studenti.map((student, index) =>
          <tr key={index}>
            <td>{student.plne_meno}</td>
            <td>{student.sp_skratka}</td>
            <td>{student.rocnik}</td>
            <td>{student.email &&
                    <a href={"mailto:" + student.email}>{student.email}</a>}
            </td>
            <td>{student.datum_prihlasenia}</td>
          </tr>
        )}
      </tbody>
      {message && <tfoot><tr><td colSpan={DetailPredmetuStudentiColumns.length}>{message}</td></tr></tfoot>}
    </table>;
  },

  renderTitle() {
    var cache = new CacheRequester();
    var {modalAkademickyRok, modalPredmetKey} = this.props.query;

    var data = this.getZapisaniStudenti(cache, modalPredmetKey, modalAkademickyRok);

    if (!data) {
      return <Loading requests={cache.missing} />;
    }

    var [studenti, predmet] = data;

    if (!predmet) {
      return "Dáta nenájdené";
    }

    return predmet.nazov;
  },

  render() {
    return <Modal title={this.renderTitle()}>

      <h4>Informačný list predmetu</h4>
      {this.renderInformacnyListPredmetu()}
      <h4>Učitelia</h4>
      {this.renderUcitelia()}
      <h4>Zapísaní študenti</h4>
      {this.renderZapisaniStudenti()}
    </Modal>;
  }
});
