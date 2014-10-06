/** @jsx React.DOM */

(function () {


var TYPY_VYUCBY = {
  'A': 'A - povinné',
  'B': 'B - povinne voliteľné',
  'C': 'C - výberové'
};


// TODO: Pocet predmetov, sucet kreditov

Votr.MojePredmetyPageContent = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  getInitialState: function() {
    return {
      sortBy: 'akademicky_rok',
      sorted: []
    }
  },

  renderContent: function () {
    var cache = new Votr.CacheRequester();
    var {studiumKey, zapisnyListKey} = this.props.query;
    var hodnotenia = cache.get('get_hodnotenia', studiumKey, zapisnyListKey);

    if (!hodnotenia) {
      return <Votr.Loading requests={cache.missing} />;
    }

    var sortKey = this.state.sortBy;
    var sorted = this.state.sorted;
    hodnotenia.sort(function(a, b) {
        if(sorted[sortKey] == 'dsc')
          b = [a, a = b][0];

        if(sortKey == 'akademicky_rok'){
          if(a[sortKey] == b[sortKey]){
            a = a['semester'];
            b = b['semester'];
            return a > b ? -1 : (a < b ? 1 : 0);
          }
        }

        a = a[sortKey];
        b = b[sortKey];

        if(sortKey == 'hodn_datum') {
          a = new Date(a.substring(6, 10), a.substring(3, 5), a.substring(0, 2));
          b = new Date(b.substring(6, 10), b.substring(3, 5), b.substring(0, 2));
        }

        return a < b ? -1 : (a > b ? 1 : 0);
    });

    return <table>
      <thead>
        <tr>
          <th onClick={this.handleSort.bind(null, 'akademicky_rok')}>Ak. rok {this.getOrder('akademicky_rok')}</th>
          <th onClick={this.handleSort.bind(null, 'semester')}>Semester {this.getOrder('semester')}</th>
          <th onClick={this.handleSort.bind(null, 'nazov')}>Názov predmetu {this.getOrder('nazov')}</th>
          <th onClick={this.handleSort.bind(null, 'skratka')}>Skratka {this.getOrder('skratka')}</th>
          <th onClick={this.handleSort.bind(null, 'kredit')}>Kredit {this.getOrder('kredit')}</th>
          <th onClick={this.handleSort.bind(null, 'typ_vyucby')}>Typ výučby {this.getOrder('typ_vyucby')}</th>
          <th onClick={this.handleSort.bind(null, 'hodn_znamka')}>Hodnotenie {this.getOrder('hodn_znamka')}</th>
          <th onClick={this.handleSort.bind(null, 'hodn_datum')}>Dátum hodnotenia {this.getOrder('hodn_datum')}</th>
          <th onClick={this.handleSort.bind(null, 'hodn_termin')}>Termín hodnotenia {this.getOrder('hodn_termin')}</th>
        </tr>
      </thead>
      <tbody>
        {hodnotenia.map((hodnotenie) =>
          <tr key={hodnotenie.key} className={hodnotenie.semester == 'Z' ? 'zima' : 'leto'}>
            <td>{hodnotenie.akademicky_rok}</td>
            <td>{hodnotenie.semester}</td>
            <td>{hodnotenie.nazov}</td>
            <td>{hodnotenie.skratka}</td>
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
