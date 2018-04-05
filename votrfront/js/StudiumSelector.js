
import { CacheRequester, Loading } from './ajax';
import { Link } from './router';
import { sortAs } from './sorting';


// TODO: Reduce code duplication with ZapisnyListSelector.


export var StudiumSelector = createReactClass({
  propTypes: {
    query: PropTypes.object.isRequired,
    component: PropTypes.func.isRequired
  },

  getItems(cache) {
    var studia = cache.get('get_studia');

    var items = studia || [];

    return _.sortBy(items, (item) => sortAs.date(item.zaciatok)).reverse();
  },

  renderSelector(cache, items, query) {
    return <ul className="nav nav-pills selector">
      <li><span className="text-pill">Štúdium:</span></li>
      {items.map((studium) => {
        var key = studium.studium_key;
        var active = key == query.studiumKey;
        return <li key={key} className={active ? "active" : ""}>
          <Link href={{ ...query, studiumKey: key }}>
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
      query = { ...query, studiumKey: mostRecentItem.studium_key };
    }

    return <div>
      {this.renderSelector(cache, items, query)}
      {this.renderPage(cache, items, query)}
    </div>;
  }
});
