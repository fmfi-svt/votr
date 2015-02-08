(function () {


function withKeys(oldQuery, zapisnyListKey) {
  return _.assign({}, oldQuery, { zapisnyListKey });
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
      var zapisneListy = cache.get('get_zapisne_listy', studium.studium_key);
      if (zapisneListy) zapisneListy.forEach((zapisnyList) => {
        items.push({ studium, zapisnyList });
      });
    });

    items = _.sortBy(items, (item) => Votr.sortAs.date(item.zapisnyList.datum_zapisu)).reverse();

    return items;
  },

  renderSelector: function (cache, items, query) {
    return <ul className="nav nav-pills selector">
      <li><span className="text-pill">Zápisný list:</span></li>
      {items.map((item) => {
        var { studium, zapisnyList } = item;
        var key = zapisnyList.zapisny_list_key;
        var active = zapisnyList.zapisny_list_key == query.zapisnyListKey;
        return <li key={key} className={active ? "active" : ""}>
          <Votr.Link href={withKeys(query, zapisnyList.zapisny_list_key)}>
            {zapisnyList.akademicky_rok} {zapisnyList.sp_skratka}
          </Votr.Link>
        </li>;
      })}
      {cache.loadedAll ? null :
        <li><span className="text-pill">
          <Votr.Loading requests={cache.missing} />
        </span></li>}
    </ul>;
  },

  renderPage: function (cache, items, query) {
    if (query.zapisnyListKey) {
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

    if (!query.zapisnyListKey && cache.loadedAll && items.length) {
      var mostRecentItem = items[0];
      query = withKeys(query, mostRecentItem.zapisnyList.zapisny_list_key);
    }

    return <div>
      {this.renderSelector(cache, items, query)}
      {this.renderPage(cache, items, query)}
    </div>;
  }
});


})();
