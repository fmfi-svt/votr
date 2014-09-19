/** @jsx React.DOM */

(function () {


// TODO: Oddelit Aktualne terminy hodnotenia vs Stare terminy hodnotenia
// TODO: Prihlas/odhlas
// TODO: Znamka (priradena / nepriradena k terminu)
// TODO: Zoznam prihlasenych (modal?)
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
          {/* TODO <th>Odhlás</th> */}
          {/* TODO <th>Známka</th> */}
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
            <td>{termin.pocet_prihlasenych +
                 (termin.maximalne_prihlasenych ? "/" + termin.maximalne_prihlasenych : "")}</td>
            <td>{termin.poznamka}</td>
            <td>{termin.prihlasovanie}</td>
            <td>{termin.odhlasovanie}</td>
            {/* TODO Odhlás */}
            {/* TODO Známka */}
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
