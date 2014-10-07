/** @jsx React.DOM */

(function () {

// TODO: Reduce code duplication with ZapisnyListSelector.


function withKeys(oldQuery, studiumKey) {
  return _.assign({}, oldQuery, { studiumKey });
}


Votr.StudiumSelector = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired,
    component: React.PropTypes.func.isRequired
  },

  getItems: function (cache) {
    var studia = cache.get('get_studia');

    var items = [];

    if (studia) studia.forEach((studium) => {
      items.push({ studium });
    });

    return items;
  },

  renderSelector: function (cache, items, query) {
    return <div className="selector">
      {items.map((item) => {
        var { studium } = item;
        var key = studium.key;
        var active = studium.key == query.studiumKey;
        return <div key={key} className={active ? "active" : ""}>
          <Votr.Link href={withKeys(query, studium.key)}>
            {studium.sp_skratka}
          </Votr.Link>
        </div>;
      })}
      {cache.loadedAll ? null : <Votr.Loading requests={cache.missing} />}
    </div>;
  },

  renderPage: function (cache, items, query) {
    if (query.studiumKey) {
      return <this.props.component query={query} />;
    }
    if (cache.loadedAll && items.length == 0) {
      return <p>Žiadne štúdiá.</p>;
    }
    return null;
  },

  render: function () {
    var cache = new Votr.CacheRequester();
    var items = this.getItems(cache);
    var query = this.props.query;

    if (!query.studiumKey && cache.loadedAll && items.length) {
      var mostRecentItem = _.max(items, (item) => Votr.sortAs.date(item.studium.zaciatok));
      query = withKeys(query, mostRecentItem.studium.key);
    }

    return <div>
      {this.renderSelector(cache, items, query)}
      {this.renderPage(cache, items, query)}
    </div>;
  }
});


})();
