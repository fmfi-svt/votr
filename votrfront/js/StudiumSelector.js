
import { CacheRequester, Loading } from './ajax';
import { Link } from './router';
import { sortAs } from './sorting';


// TODO: Reduce code duplication with ZapisnyListSelector.


function withKeys(oldQuery, studiumKey) {
  return _.assign({}, oldQuery, { studiumKey });
}


export var StudiumSelector = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired,
    component: React.PropTypes.func.isRequired
  },

  getItems(cache) {
    var studia = cache.get('get_studia');

    var items = [];

    if (studia) studia.forEach((studium) => {
      items.push({ studium });
    });

    items = _.sortBy(items, (item) => sortAs.date(item.studium.zaciatok)).reverse();

    return items;
  },

  renderSelector(cache, items, query) {
    return <ul className="nav nav-pills selector">
      <li><span className="text-pill">Štúdium:</span></li>
      {items.map((item) => {
        var { studium } = item;
        var key = studium.studium_key;
        var active = studium.studium_key == query.studiumKey;
        return <li key={key} className={active ? "active" : ""}>
          <Link href={withKeys(query, studium.studium_key)}>
            {studium.sp_skratka}
          </Link>
        </li>;
      })}
      {cache.loadedAll ? null :
        <li><span className="text-pill">
          <Loading requests={cache.missing} />
        </span></li>}
    </ul>;
  },

  renderPage(cache, items, query) {
    if (query.studiumKey) {
      return <this.props.component query={query} />;
    }
    if (cache.loadedAll && items.length == 0) {
      return <p>Žiadne štúdiá.</p>;
    }
    return null;
  },

  render() {
    var cache = new CacheRequester();
    var items = this.getItems(cache);
    var query = this.props.query;

    if (!query.studiumKey && cache.loadedAll && items.length) {
      var mostRecentItem = items[0];
      query = withKeys(query, mostRecentItem.studium.studium_key);
    }

    return <div>
      {this.renderSelector(cache, items, query)}
      {this.renderPage(cache, items, query)}
    </div>;
  }
});
