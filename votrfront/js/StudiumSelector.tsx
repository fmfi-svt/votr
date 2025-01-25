import { sortBy } from "lodash-es";
import React, { useContext } from "react";
import { CacheRequester, Loading } from "./ajax";
import { QueryContext, RelativeLink } from "./router";
import { sortAs } from "./sorting";

// TODO: Reduce code duplication with ZapisnyListSelector.

export function StudiumSelector({ children }: { children: React.ReactNode }) {
  let query = useContext(QueryContext);
  const cache = new CacheRequester();
  const studia = cache.get("get_studia") || [];
  const items = sortBy(studia, (item) => sortAs.date(item.zaciatok)).reverse();

  if (!query.studiumKey && cache.loadedAll && items[0]) {
    const mostRecentItem = items[0];
    query = { ...query, studiumKey: mostRecentItem.studium_key };
  }

  return (
    <React.Fragment>
      <ul className="nav nav-pills selector">
        <li>
          <span className="text-pill">Štúdium:</span>
        </li>
        {items.map((studium, index) => {
          const studiumKey = studium.studium_key;
          const active = studiumKey == query.studiumKey;
          return (
            <li key={index} className={active ? "active" : ""}>
              <RelativeLink href={{ studiumKey }}>
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
      {query.studiumKey ?
        <QueryContext value={query}>{children}</QueryContext>
      : cache.loadedAll && items.length == 0 ?
        <p>Žiadne štúdiá.</p>
      : null}
    </React.Fragment>
  );
}
