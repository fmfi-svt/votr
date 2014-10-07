/** @jsx React.DOM */

(function () {


// TODO: Oddelit Aktualne terminy hodnotenia vs Stare terminy hodnotenia
// TODO: Prihlas/odhlas
// TODO: Sorting

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

    return <table>
      <thead>
        <tr>
          <th>Predmet</th>
          <th>Dátum</th>
          <th>Čas</th>
          <th>Miestnosť</th>
          <th>Hodnotiaci</th>
          <th>Prihlásení</th>
          <th>Poznámka</th>
          <th>Prihlasovanie</th>
          <th>Odhlasovanie</th>
          <th>Známka</th>
          {/* TODO <th>Odhlás</th> */}
        </tr>
      </thead>
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
