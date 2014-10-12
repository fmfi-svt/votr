/** @jsx React.DOM */

(function () {


var TYPY_VYUCBY = {
  'A': 'A - povinné',
  'B': 'B - povinne voliteľné',
  'C': 'C - výberové'
};

Votr.MojePredmetyColumns = [
  ["Semester", 'semester', null, true],
  ["Skratka", 'skratka'],
  ["Názov predmetu", 'nazov'],
  ["Kredit", 'kredit', Votr.sortAs.number],
  ["Typ výučby", 'typ_vyucby'],
  ["Hodnotenie", 'hodn_znamka'],
  ["Dátum hodnotenia", 'hodn_datum', Votr.sortAs.date],
  ["Termín hodnotenia", 'hodn_termin']
];
Votr.MojePredmetyColumns.defaultOrder = 'd0a2';


Votr.MojePredmetyPageContent = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  renderContent: function () {
    var cache = new Votr.CacheRequester();
    var {studiumKey, zapisnyListKey} = this.props.query;
    var hodnotenia = cache.get('get_hodnotenia', studiumKey, zapisnyListKey);

    if (!hodnotenia) {
      return <Votr.Loading requests={cache.missing} />;
    }

    var [hodnotenia, header] = Votr.sortTable(
      hodnotenia, Votr.MojePredmetyColumns, this.props.query, 'predmetySort');

    var coursesStats = Votr.coursesStats(hodnotenia);

    return <table>
      <thead>{header}</thead>
      <tbody>
        {hodnotenia.map((hodnotenie) =>
          <tr key={hodnotenie.key} className={hodnotenie.semester == 'Z' ? 'zima' : 'leto'}>
            <td>{hodnotenie.semester}</td>
            <td>{hodnotenie.skratka}</td>
            <td>{hodnotenie.nazov}</td>
            <td>{hodnotenie.kredit}</td>
            <td>{TYPY_VYUCBY[hodnotenie.typ_vyucby] || hodnotenie.typ_vyucby}</td>
            <td>
              {hodnotenie.hodn_znamka}
              {hodnotenie.hodn_znamka ? " - " : null}
              {hodnotenie.hodn_znamka_popis}
            </td>
            <td>{hodnotenie.hodn_datum}</td>
            <td>{hodnotenie.hodn_termin}</td>
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
