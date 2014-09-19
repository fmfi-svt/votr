/** @jsx React.DOM */

(function () {


var TYPY_VYUCBY = {
  'A': 'A - povinné',
  'B': 'B - povinne voliteľné',
  'C': 'C - výberové'
};


// TODO: Sorting
// TODO: Pocet predmetov, sucet kreditov

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

    return <table>
      <thead>
        <tr>
          <th>Semester</th>
          <th>Skratka</th>
          <th>Názov predmetu</th>
          <th>Kredit</th>
          <th>Typ výučby</th>
          <th>Hodnotenie</th>
          <th>Dátum hodnotenia</th>
          <th>Termín hodnotenia</th>
        </tr>
      </thead>
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
