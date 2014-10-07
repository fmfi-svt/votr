/** @jsx React.DOM */

(function () {


// TODO: Oddelit Aktualne terminy hodnotenia vs Stare terminy hodnotenia
// TODO: Prihlas/odhlas


Votr.MojeSkuskyColumns = [
  ["Predmet", 'nazov_predmetu'],
  ["Dátum", 'datum', Votr.sortAs.date],
  ["Čas", 'cas'],
  ["Miestnosť", 'miestnost'],
  ["Hodnotiaci", 'hodnotiaci', Votr.sortAs.personName],
  ["Prihlásení", 'pocet_prihlasenych', Votr.sortAs.number],
  ["Poznámka", 'poznamka'],
  ["Prihlasovanie", 'prihlasovanie', Votr.sortAs.interval],
  ["Odhlasovanie", 'odhlasovanie', Votr.sortAs.interval],
  ["Známka", null, (termin) => termin.hodnotenie_terminu || termin.hodnotenie_predmetu]
  // TODO: "Odhlás"
];


Votr.MojeSkuskyPageContent = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  renderContent: function () {
    var cache = new Votr.CacheRequester();
    var {studiumKey, zapisnyListKey} = this.props.query;
    var terminy = cache.get('get_prihlasene_terminy', studiumKey, zapisnyListKey);

    if (!terminy) {
      return <Votr.Loading requests={cache.missing} />;
    }

    var [terminy, header] = Votr.sortTable(
      terminy, Votr.MojeSkuskyColumns, this.props.query, 'skuskySort');

    return <table>
      <thead>{header}</thead>
      <tbody>
        {terminy.map((termin) =>
          <tr key={termin.key}>
            <td>{termin.nazov_predmetu}</td>
            <td>{termin.datum}</td>
            <td>{termin.cas}</td>
            <td>{termin.miestnost}</td>
            <td>{termin.hodnotiaci}</td>
            <td><Votr.Link href={_.assign({}, this.props.query, { action: 'zoznamPrihlasenychNaTermin', predmetKey: termin.skratka_predmetu, terminKey: termin.key })}>
              {termin.pocet_prihlasenych + 
               (termin.maximalne_prihlasenych ? "/" + termin.maximalne_prihlasenych : "")}
            </Votr.Link></td>
            <td>{termin.poznamka}</td>
            <td>{termin.prihlasovanie}</td>
            <td>{termin.odhlasovanie}</td>
            <td>
              {termin.hodnotenie_terminu ? termin.hodnotenie_terminu :
               termin.hodnotenie_predmetu ? termin.hodnotenie_predmetu + ' (nepriradená k termínu)' :
               null}
            </td>
            {/* TODO Odhlás */}
          </tr>
        )}
      </tbody>
    </table>;
  },

  render: function () {
    return <div>
      <Votr.PageTitle>Moje skúšky</Votr.PageTitle>
      {this.renderContent()}
    </div>;
  }
});


Votr.MojeSkuskyPage = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  render: function () {
    return <Votr.PageLayout query={this.props.query}>
      <Votr.ZapisnyListSelector query={this.props.query} component={Votr.MojeSkuskyPageContent} />
    </Votr.PageLayout>;
  }
});


})();
