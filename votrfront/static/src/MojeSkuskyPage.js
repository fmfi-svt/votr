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
    var sorted = this.state.sorted;
    terminy.sort(function(a, b) {
        a = a[sortKey];
        b = b[sortKey];

        if(sorted[sortKey] == 'dsc')
          b = [a, a = b][0];

        if(sortKey == 'datum') {
           a = new Date(a.substring(6, 10), a.substring(3, 5), a.substring(0, 2));
           b = new Date(b.substring(6, 10), b.substring(3, 5), b.substring(0, 2));
        }

        return a < b ? -1 : (a > b ? 1 : 0);
    });

    return <table>
      <thead>
        <tr>
          <th onClick={this.handleSort.bind(null, 'nazov_predmetu')}>Predmet {this.getOrder('nazov_predmetu')}</th>
          <th onClick={this.handleSort.bind(null, 'datum')}>Dátum {this.getOrder('datum')}</th>
          <th onClick={this.handleSort.bind(null, 'cas')}>Čas {this.getOrder('cas')}</th>
          <th onClick={this.handleSort.bind(null, 'miestnost')}>Miestnosť {this.getOrder('miestnost')}</th>
          <th onClick={this.handleSort.bind(null, 'hodnotiaci')}>Hodnotiaci {this.getOrder('hodnotiaci')}</th>
          <th onClick={this.handleSort.bind(null, 'pocet_prihlasenych')}>Prihlásení {this.getOrder('pocet_prihlasenych')}</th>
          <th onClick={this.handleSort.bind(null, 'poznamka')}>Poznámka {this.getOrder('poznamka')}</th>
          <th onClick={this.handleSort.bind(null, 'prihlasovanie')}>Prihlasovanie {this.getOrder('prihlasovanie')}</th>
          <th onClick={this.handleSort.bind(null, 'odhlasovanie')}>Odhlasovanie {this.getOrder('odhlasovanie')}</th>
          <th onClick={this.handleSort.bind(null, 'hodnotenie_terminu')}>Hodnotenie termínu {this.getOrder('hodnotenie_terminu')}</th>
          <th onClick={this.handleSort.bind(null, 'hodnotenie_predmetu')}>Hodnotenie predmetu {this.getOrder('hodnotenie_predmetu')}</th>
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

  getOrder: function(sortKey) {
    if(typeof this.state.sorted[sortKey] === 'undefined')
      return null;
    if(this.state.sorted[sortKey] === 'asc')
      return <span className="ascending"></span>;
    return <span className="descending"></span>;
  },

  handleSort: function(sortKey) {
    var update = {};
    update['sortBy'] = sortKey;
    update['sorted'] = this.state.sorted;
    update['sorted'][sortKey] = (update['sorted'][sortKey] != 'asc') ? 'asc' : 'dsc';
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
