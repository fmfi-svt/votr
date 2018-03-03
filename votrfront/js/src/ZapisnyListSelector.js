import React, { Component } from 'react';
import PropTypes from 'prop-types';

import { CacheRequester, Loading } from './ajax';
import { Link } from './router';
import { sortAs } from './sorting';

export class ZapisnyListSelector extends Component {
  getItems = (cache) => {
    const studia = cache.get('get_studia');
    const items = [];

    if (studia) {
      studia.forEach((studium) => {
        const zapisneListy = cache.get('get_zapisne_listy', studium.studium_key);
        if (zapisneListy) {
          items.push(...zapisneListy);
        }
      });
    }

    return items.sort((a, b) => {
      const d1 = sortAs.date(a.datum_zapisu);
      const d2 = sortAs.date(b.datum_zapisu);

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
        <li>
          <span className="text-pill">
            Zápisný list:
          </span>
        </li>
        {items.map((zapisnyList) => {
          const key = zapisnyList.zapisny_list_key;
          const active = key === query.zapisnyListKey;
          return (
            <li key={key} className={active ? 'active' : ''}>
              <Link href={{ ...query, zapisnyListKey: key }}>
                {zapisnyList.akademicky_rok} {zapisnyList.sp_skratka}
              </Link>
            </li>
          );
        })}
        {cache.loadedAll ? null : (
          <li><span className="text-pill">
            <Loading requests={cache.missing} />
          </span></li>
        )}
      </ul>
    );
  }

  renderPage = (cache, items, query) => {
    if (query.zapisnyListKey) {
      return <this.props.component query={query} />;
    }
    if (cache.loadedAll && items.length === 0) {
      return <p>Žiadne zápisné listy.</p>;
    }
    return null;
  }

  render() {
    const cache = new CacheRequester();
    const items = this.getItems(cache);
    let query = this.props.query;

    if (!query.zapisnyListKey && cache.loadedAll && items.length) {
      const mostRecentItem = items[0];
      query = { ...query, zapisnyListKey: mostRecentItem.zapisny_list_key };
    }

    return (
      <div>
        {this.renderSelector(cache, items, query)}
        {this.renderPage(cache, items, query)}
      </div>
    );
  }
}

ZapisnyListSelector.propTypes = {
  query: PropTypes.object.isRequired,
  component: PropTypes.func.isRequired,
};
