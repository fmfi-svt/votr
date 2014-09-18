/** @jsx React.DOM */

(function () {


function dateToInteger(date) {
  if (date == '') return 0;
  if (!date.match(/^\d\d\.\d\d\.\d\d\d\d$/)) throw Error('Bad date format');
  return parseInt(
    date.substring(6, 10) + date.substring(3, 5) + date.substring(0, 2), 10);
}


function withKeys(oldQuery, studiumKey, zapisnyListKey) {
  return _.assign({}, oldQuery, { studiumKey, zapisnyListKey });
}


Votr.ZapisnyListSelector = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired,
    component: React.PropTypes.func.isRequired
  },

  getItems: function (cache) {
    var studia = cache.get('get_studia');

    var items = [];

    if (studia) studia.forEach((studium) => {
      var zapisneListy = cache.get('get_zapisne_listy', studium.key);
      if (zapisneListy) zapisneListy.forEach((zapisnyList) => {
        var sortValue = dateToInteger(zapisnyList.datum_zapisu);
        items.push({ studium, zapisnyList, sortValue });
      });
    });

    return items;
  },

  renderSelector: function (cache, items, query) {
    return <div className="selector">
      {items.map((item) => {
        var { studium, zapisnyList } = item;
        var key = studium.key + '.' + zapisnyList.key;
        var active = studium.key == query.studiumKey && zapisnyList.key == query.zapisnyListKey;
        return <div key={key} className={active ? "active" : ""}>
          <Votr.Link href={withKeys(query, studium.key, zapisnyList.key)}>
            {zapisnyList.akademicky_rok} {zapisnyList.sp_skratka}
          </Votr.Link>
        </div>;
      })}
      {cache.loadedAll ? null : <Votr.Loading requests={cache.missing} />}
    </div>;
  },

  renderPage: function (cache, items, query) {
    if (query.studiumKey && query.zapisnyListKey) {
      return <this.props.component query={query} />;
    }
    if (cache.loadedAll && items.length == 0) {
      return <p>Žiadne zápisné listy.</p>;
    }
    return null;
  },

  render: function () {
    var cache = new Votr.CacheRequester();
    var items = this.getItems(cache);
    var query = this.props.query;

    if (!(query.studiumKey && query.zapisnyListKey) && cache.loadedAll && items.length) {
      var mostRecentItem = _.max(items, 'sortValue');
      query = withKeys(query, mostRecentItem.studium.key, mostRecentItem.zapisnyList.key);
    }

    return <div>
      {this.renderSelector(cache, items, query)}
      {this.renderPage(cache, items, query)}
    </div>;
  }
});


})();
