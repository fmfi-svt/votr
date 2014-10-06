/** @jsx React.DOM */

(function () {


// TODO: Oddelit Aktualne terminy hodnotenia vs Stare terminy hodnotenia
// TODO: Prihlas/odhlas
// TODO: Zoznam prihlasenych (modal?)

Votr.MojeSkuskyPageContent = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  getInitialState: function() {
    return {
      sortBy: 'nazov_predmetu',
      sortType: 'string',
      sorted: []
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
    var sortType = this.state.sortType;
    var sorted = this.state.sorted;
    terminy.sort(function(a, b) {
        a = a[sortKey];
        b = b[sortKey];
        if(sorted[sortKey] == 'dsc')
          b = [a, a = b][0];

        if(sortType == 'date')
          return (new Date(a.substring(6, 10), a.substring(3, 5), a.substring(0, 2)) - new Date(b.substring(6, 10), b.substring(3, 5), b.substring(0, 2)));

        return a < b ? -1 : (a > b ? 1 : 0);
    });

    return <table>
      <thead>
        <tr>
          <th onClick={this.handleSort.bind(null, 'nazov_predmetu')}>Predmet</th>
          <th onClick={this.handleSort.bind(null, 'datum', 'date')}>Dátum</th>
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
          </tr>
        )}
      </tbody>
    </table>;
  },

  handleSort: function(sortKey, type) {
    var update = {};
    update['sortBy'] = sortKey;
    update['sorted'] = this.state.sorted;
    update['sorted'][sortKey] = (update['sorted'][sortKey] != 'asc') ? 'asc' : 'dsc';
    update['sortType'] = type;
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
