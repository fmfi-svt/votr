/** @jsx React.DOM */

(function () {

Votr.DetailPredmetuUciteliaColumns = [
  ["Meno", 'plne_meno', Votr.sortAs.personName],
  ["typ", 'typ']
];
Votr.DetailPredmetuUciteliaColumns.defaultOrder = 'a0';

Votr.DetailPredmetuStudentiColumns = Votr.ZoznamPrihlasenychNaTerminColumns.slice();
Votr.DetailPredmetuStudentiColumns.defaultOrder = 'a0';

Votr.DetailPredmetuContent = React.createClass({
  getZapisaniStudenti: function(cache, predmetKey, akademickyRok){
    return cache.get('get_studenti_zapisani_na_predmet', predmetKey, akademickyRok);
  },

  renderUcitelia: function () {
    var cache = new Votr.CacheRequester();
    var {fakulta, akademickyRok, predmetKey} = this.props.query;

    var data = this.getZapisaniStudenti(cache, predmetKey, akademickyRok);

    if (!data) {
      return <Votr.Loading requests={cache.missing} />;
    }

    var [studenti, predmet] = data;

    var ucitelia = cache.get('get_ucitelia_predmetu', predmetKey, fakulta, akademickyRok, predmet.semester);

    if (!ucitelia) {
      return <Votr.Loading requests={cache.missing} />;
    }

    var [ucitelia, header] = Votr.sortTable(
      ucitelia, Votr.DetailPredmetuUciteliaColumns, this.props.query, 'uciteliaSort');

    return <table>
      <thead>{header}</thead>
      <tbody>
        {ucitelia.map((ucitel, index) =>
          <tr key={index}>
            <td>{ucitel.plne_meno}</td>
            <td>{ucitel.typ}</td>
          </tr>
        )}
      </tbody>
    </table>;
  },

  renderZapisaniStudenti: function () {
    var cache = new Votr.CacheRequester();
    var {akademickyRok, predmetKey} = this.props.query;

    var data = this.getZapisaniStudenti(cache, predmetKey, akademickyRok);

    if (!data) {
      return <Votr.Loading requests={cache.missing} />;
    }

    var [studenti, predmet] = data;

    var [studenti, header] = Votr.sortTable(
      studenti, Votr.DetailPredmetuStudentiColumns, this.props.query, 'studentiSort');

    return <table>
      <thead>{header}</thead>
      <tbody>
        {studenti.map((student, index) =>
          <tr key={index}>
            <td>{student.plne_meno}</td>
            <td>{student.rocnik}</td>
            <td>{student.sp_skratka}</td>
            <td>{student.email}</td>
            <td>{student.datum_prihlasenia}</td>
          </tr>
        )}
      </tbody>
    </table>;
  },

  renderTitle: function() {
    var cache = new Votr.CacheRequester();
    var {akademickyRok, predmetKey} = this.props.query;

    var data = this.getZapisaniStudenti(cache, predmetKey, akademickyRok);

    if (!data) {
      return <Votr.Loading requests={cache.missing} />;
    }

    var [studenti, predmet] = data;

    return predmet.nazov;
  },

  render: function () {
    return <div>
      <Votr.PageTitle>{this.renderTitle()}</Votr.PageTitle>
      <h2>Učitelia</h2>
      {this.renderUcitelia()}
      <h2>Zapísaní študenti</h2>
      {this.renderZapisaniStudenti()}
    </div>;
  }
});


Votr.DetailPredmetuPage = React.createClass({
  render: function () {
    return <Votr.PageLayout query={this.props.query}>
        <Votr.DetailPredmetuContent query={this.props.query} />
    </Votr.PageLayout>;
  }
});


})();
