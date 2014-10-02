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

  getInitialState: function() {
    return {
      currentDirection: 'asc',
      sortBy: 'nazov_predmetu'
    }
  },

  renderContent: function () {
    var cache = new Votr.CacheRequester();
    var {studiumKey, zapisnyListKey} = this.props.query;
    var terminy = cache.get('get_prihlasene_terminy', studiumKey, zapisnyListKey);

    if (!terminy) {
      return <Votr.Loading requests={cache.missing} />;
    }

    var sortKey = this.state.sortBy;
    terminy.sort(function(a, b) {
        a = a[sortKey];
        b = b[sortKey];

        return a < b ? -1 : (a > b ? 1 : 0);
    });

    return <table>
      <thead>
        <tr>
          <th onClick={this.handleSort.bind(null, 'nazov_predmetu')}>Predmet</th>
          <th onClick={this.handleSort.bind(null, 'datum')}>Dátum</th>
          <th onClick={this.handleSort.bind(null, 'cas')}>Čas</th>
          <th onClick={this.handleSort.bind(null, 'miestnost')}>Miestnosť</th>
          <th onClick={this.handleSort.bind(null, 'hodnotiaci')}>Hodnotiaci</th>
          <th onClick={this.handleSort.bind(null, 'pocet_prihlasenych')}>Prihlásení</th>
          <th onClick={this.handleSort.bind(null, 'poznamka')}>Poznámka</th>
          <th onClick={this.handleSort.bind(null, 'prihlasovanie')}>Prihlasovanie</th>
          <th onClick={this.handleSort.bind(null, 'odhlasovanie')}>Odhlasovanie</th>
          <th onClick={this.handleSort.bind(null, 'hodnotenie_terminu')}>Hodnotenie termínu</th>
          <th onClick={this.handleSort.bind(null, 'hodnotenie_predmetu')}>Hodnotenie predmetu</th>
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
            <td>{termin.hodnotenie_terminu}</td>
            <td>{termin.hodnotenie_predmetu}</td>
            {/* TODO Odhlás */}
            {/* TODO Známka */}
          </tr>
        )}
      </tbody>
    </table>;
  },

  handleSort: function(sortKey) {
    var update = {};
    update['sortBy'] = sortKey;
    this.setState(update);
    
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
