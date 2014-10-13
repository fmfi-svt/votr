/** @jsx React.DOM */

(function () {


Votr.ZoznamPrihlasenychNaTerminColumns = [
  ["Meno", 'plne_meno', Votr.sortAs.personName],
  ["Študijný program", 'sp_skratka'],
  ["Ročník", 'rocnik', Votr.sortAs.number],
  ["E-mail", 'email'],
  ["Dátum prihlásenia", 'datum_prihlasenia', Votr.sortAs.date]
];


Votr.ZoznamPrihlasenychNaTerminPageContent = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  renderContent: function () {
    var cache = new Votr.CacheRequester();
    var {studiumKey, zapisnyListKey, predmetKey, terminKey} = this.props.query;

    if (!(predmetKey && terminKey && studiumKey && zapisnyListKey)) return null;
    var studenti = cache.get('get_prihlaseni_studenti', studiumKey, zapisnyListKey, [predmetKey], terminKey);

    if (!studenti) {
      return <Votr.Loading requests={cache.missing} />;
    }

    var [studenti, header] = Votr.sortTable(
      studenti, Votr.ZoznamPrihlasenychNaTerminColumns,
      this.props.query, 'studentiSort');

    return <table className="table table-condensed table-bordered table-striped table-hover">
      <thead>{header}</thead>
      <tbody>
        {studenti.map((student, index) =>
          <tr key={index}>
            <td>{student.plne_meno}</td>
            <td>{student.sp_skratka}</td>
            <td>{student.rocnik}</td>
            <td>{student.email}</td>
            <td>{student.datum_prihlasenia}</td>
          </tr>
        )}
      </tbody>
    </table>;
  },

  render: function () {
    return <div>
      <Votr.PageTitle>Zoznam prihlásených na termín:</Votr.PageTitle>
      {this.renderContent()}
    </div>;
  }
});


Votr.ZoznamPrihlasenychNaTerminPage = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  render: function () {
    return <Votr.PageLayout query={this.props.query}>
      <Votr.ZoznamPrihlasenychNaTerminPageContent query={this.props.query} />
    </Votr.PageLayout>;
  }
});

})();
