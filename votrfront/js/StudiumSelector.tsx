import React, { useContext } from "react";
import _ from "lodash";
import { CacheRequester, Loading } from "./ajax";
import { QueryContext, RelativeLink } from "./router";
import { sortAs } from "./sorting";

// TODO: Reduce code duplication with ZapisnyListSelector.

function getItems(cache: CacheRequester) {
  var studia = cache.get("get_studia");

  var items = studia || [];

  return _.sortBy(items, (item) => sortAs.date(item.zaciatok)).reverse();
}

export function StudiumSelector(props: { children: React.ReactNode }) {
  var query = useContext(QueryContext);
  var cache = new CacheRequester();
  var items = getItems(cache);

  if (!query.studiumKey && cache.loadedAll && items[0]) {
    var mostRecentItem = items[0];
    query = { ...query, studiumKey: mostRecentItem.studium_key };
  }

  return (
    <React.Fragment>
      <ul className="nav nav-pills selector">
        <li>
          <span className="text-pill">Štúdium:</span>
        </li>
        {items.map((studium) => {
          var key = studium.studium_key;
          var active = key == query.studiumKey;
          return (
            <li key={key} className={active ? "active" : ""}>
              <RelativeLink href={{ studiumKey: key }}>
                {studium.sp_skratka}
              </RelativeLink>
            </li>
          );
        })}
        {cache.loadedAll ? null : (
          <li>
            <span className="text-pill">
              <Loading requests={cache.missing} />
            </span>
          </li>
        )}
      </ul>
      {query.studiumKey ? (
        <QueryContext.Provider value={query}>
          {props.children}
        </QueryContext.Provider>
      ) : cache.loadedAll && items.length == 0 ? (
        <p>Žiadne štúdiá.</p>
      ) : null}
    </React.Fragment>
  );
}
