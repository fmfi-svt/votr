(function () {


Votr.ZoznamPrihlasenychNaTerminColumns = [
  ["Meno", 'plne_meno', Votr.sortAs.personName],
  ["Študijný program", 'sp_skratka'],
  ["Ročník", 'rocnik', Votr.sortAs.number],
  ["E-mail", 'email'],
  ["Dátum prihlásenia", 'datum_prihlasenia', Votr.sortAs.date]
];


Votr.ZoznamPrihlasenychNaTerminModal = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  renderContent: function () {
    var cache = new Votr.CacheRequester();
    var {modalTerminKey} = this.props.query;

    if (!modalTerminKey) return null;
    var studenti = cache.get('get_prihlaseni_studenti', modalTerminKey);

    if (!studenti) {
      return <Votr.Loading requests={cache.missing} />;
    }

    var [studenti, header] = Votr.sortTable(
      studenti, Votr.ZoznamPrihlasenychNaTerminColumns,
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
            <td>{student.email}</td>
            <td>{student.datum_prihlasenia}</td>
          </tr>
        )}
      </tbody>
      {message && <tfoot><tr><td colSpan={Votr.ZoznamPrihlasenychNaTerminColumns.length}>{message}</td></tr></tfoot>}
    </table>;
  },

  render: function () {
    return <Votr.Modal title="Zoznam prihlásených na termín">
      {this.renderContent()}
    </Votr.Modal>;
  }
});


})();
