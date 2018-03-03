import React, { Component } from 'react';
import PropTypes from 'prop-types';

import { CacheRequester, Loading } from './ajax';
import { Link } from './router';
import { sortAs } from './sorting';


// TODO: Reduce code duplication with ZapisnyListSelector.

export class StudiumSelector extends Component {

  getItems = (cache) => {
    const studia = cache.get('get_studia');
    const items = studia ? [...studia] : [];

    return items.sort((a, b) => {
      const d1 = sortAs.date(a.zaciatok);
      const d2 = sortAs.date(b.zaciatok);

      if (d1 < d2) {
        return -1;
      } else if (d1 > d2) {
        return 1;
      }
      return 0;
    }).reverse();
  }

  renderSelector = (cache, items, query) => {
    return (
      <ul className="nav nav-pills selector">
        <li><span className="text-pill">Štúdium:</span></li>
        {items.map((studium) => {
          const key = studium.studium_key;
          const active = key === query.studiumKey;
          return (
            <li key={key} className={active ? 'active' : ''}>
              <Link href={{ ...query, studiumKey: key }}>
                {studium.sp_skratka}
              </Link>
            </li>
          );
        })}
        {cache.loadedAll
          ? null
          : (
            <li>
              <span className="text-pill">
                <Loading requests={cache.missing} />
              </span>
            </li>
          )
        }
      </ul>
    );
  }

  renderPage = (cache, items, query) => {
    if (query.studiumKey) {
      return <this.props.component query={query} />;
    }
    if (cache.loadedAll && items.length === 0) {
      return <p>Žiadne štúdiá.</p>;
    }
    return null;
  }

  render() {
    const cache = new CacheRequester();
    const items = this.getItems(cache);
    let query = this.props.query;

    if (!query.studiumKey && cache.loadedAll && items.length) {
      const mostRecentItem = items[0];
      query = { ...query, studiumKey: mostRecentItem.studium_key };
    }

    return (
      <div>
        {this.renderSelector(cache, items, query)}
        {this.renderPage(cache, items, query)}
      </div>
    );
  }
}

StudiumSelector.propTypes = {
  query: PropTypes.object.isRequired,
  component: PropTypes.func.isRequired,
};
