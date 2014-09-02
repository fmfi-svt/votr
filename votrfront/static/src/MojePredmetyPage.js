/**
 * @jsx React.DOM
 * @require base.js
 * @require ajax.js
 * @require ZapisnyListSelector.js
 */

(function () {

var {t, PageTitle, PageLayout, CacheRequester, Loading, ZapisnyListSelector} = Votr;


Votr.MojePredmetyPageContent = React.createClass({
  propTypes: {
    studiumKey: React.PropTypes.string.isRequired,
    zapisnyListKey: React.PropTypes.string.isRequired
  },

  render: function () {
    return <div>
      <PageTitle><t>Moje predmety</t></PageTitle>
      {this.renderContent()}
    </div>;
  },

  renderContent: function () {
    var {studiumKey, zapisnyListKey} = this.props;

    var cache = new CacheRequester();
    var hodnotenia = cache.get('get_hodnotenia', studiumKey, zapisnyListKey);

    if (!hodnotenia) {
      return <Loading requests={cache.missing} />;
    }

    var typyVyucby = {
      'A': 'A - povinné',
      'B': 'B - povinne voliteľné',
      'C': 'C - výberové'
    };

    return <table>
      <tr>
        <th><t>Semester</t></th>
        <th><t>Skratka</t></th>
        <th><t>Názov predmetu</t></th>
        <th><t>Kredit</t></th>
        <th><t>Typ výučby</t></th>
        <th><t>Hodnotenie</t></th>
        <th><t>Dátum hodnotenia</t></th>
        <th><t>Termín hodnotenia</t></th>
      </tr>
      {hodnotenia.map((hodnotenie) =>
        <tr className={hodnotenie.semester == 'Z' ? 'zima' : 'leto'}>
          <td>{hodnotenie.semester}</td>
          <td>{hodnotenie.skratka}</td>
          <td>{hodnotenie.nazov}</td>
          <td>{hodnotenie.kredit}</td>
          <td>{typyVyucby[hodnotenie.typ_vyucby] || hodnotenie.typ_vyucby}</td>
          <td>
            {hodnotenie.hodn_znamka}
            {hodnotenie.hodn_znamka ? " - " : null}
            {hodnotenie.hodn_znamka_popis}
          </td>
          <td>{hodnotenie.hodn_datum}</td>
          <td>{hodnotenie.hodn_termin}</td>
        </tr>
      )}
    </table>;
  }
});


Votr.MojePredmetyPage = React.createClass({
  propTypes: {
    route: React.PropTypes.object.isRequired
  },

  render: function () {
    return <PageLayout activeItem="mojePredmety">
      <ZapisnyListSelector route={this.props.route}
                           component={Votr.MojePredmetyPageContent} />
    </PageLayout>;
  }
});


})();
