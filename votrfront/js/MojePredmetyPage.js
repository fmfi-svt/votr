(function () {


Votr.MojePredmetyColumns = [
  [<abbr title="Semester">Sem.</abbr>, 'semester', null, true],
  ["Názov predmetu", 'nazov'],
  ["Skratka predmetu", 'skratka'],
  ["Kredit", 'kredit', Votr.sortAs.number],
  ["Typ výučby", 'typ_vyucby'],
  ["Hodnotenie", 'hodn_znamka'],
  ["Dátum hodnotenia", 'hodn_datum', Votr.sortAs.date],
  ["Termín hodnotenia", 'hodn_termin']
];
Votr.MojePredmetyColumns.defaultOrder = 'd0a1';


Votr.MojePredmetyPageContent = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  renderContent: function () {
    var cache = new Votr.CacheRequester();
    var {studiumKey, zapisnyListKey} = this.props.query;
    var [hodnotenia, message] = cache.get('get_hodnotenia', studiumKey, zapisnyListKey) || [];

    if (!hodnotenia) {
      return <Votr.Loading requests={cache.missing} />;
    }

    var [hodnotenia, header] = Votr.sortTable(
      hodnotenia, Votr.MojePredmetyColumns, this.props.query, 'predmetySort');

    var coursesStats = Votr.coursesStats(hodnotenia);

    return <table className="table table-condensed table-bordered table-striped table-hover">
      <thead>{header}</thead>
      <tbody>
        {hodnotenia.map((hodnotenie) =>
          <tr key={hodnotenie.key} className={Votr.classForSemester(hodnotenie.semester)}>
            <td>{hodnotenie.semester}</td>
            <td><Votr.Link href={_.assign({}, this.props.query, { modal: 'detailPredmetu', modalPredmetKey: hodnotenie.key, modalAkademickyRok: hodnotenie.akademicky_rok})}>
              {hodnotenie.nazov}
            </Votr.Link></td>
            <td>{hodnotenie.skratka}</td>
            <td>{hodnotenie.kredit}</td>
            <td>{Votr.humanizeTypVyucby(hodnotenie.typ_vyucby)}</td>
            <td>
              {hodnotenie.hodn_znamka}
              {hodnotenie.hodn_znamka ? " - " : null}
              {hodnotenie.hodn_znamka_popis}
            </td>
            <td>{hodnotenie.hodn_datum}</td>
            <td>{Votr.humanizeTerminHodnotenia(hodnotenie.hodn_termin)}</td>
          </tr>
        )}
      </tbody>
      <tfoot>
          <tr>
            <td colSpan="3">Celkom {coursesStats.spolu.count} predmetov ({coursesStats.zima.count} v zime, {coursesStats.leto.count} v lete)</td>
            <td>{coursesStats.spolu.creditsCount} ({coursesStats.zima.creditsCount}+{coursesStats.leto.creditsCount})</td>
            <td></td>
            <td>{Votr.renderWeightedStudyAverage(hodnotenia)}</td>
            <td></td>
            <td></td>
          </tr>
          {message && <tr><td colSpan="8">{message}</td></tr>}
      </tfoot>
    </table>;
  },

  render: function () {
    return <div>
      <Votr.PageTitle>Moje predmety</Votr.PageTitle>
      {this.renderContent()}
    </div>;
  }
});


Votr.MojePredmetyPage = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  render: function () {
    return <Votr.PageLayout query={this.props.query}>
      <Votr.ZapisnyListSelector query={this.props.query} component={Votr.MojePredmetyPageContent} />
    </Votr.PageLayout>;
  }
});


})();
