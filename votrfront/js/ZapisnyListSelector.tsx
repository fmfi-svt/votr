import { sortBy } from "lodash-es";
import React, { useContext } from "react";
import { CacheRequester, Loading } from "./ajax";
import { currentAcademicYear } from "./coursesStats";
import { Link, QueryContext, RelativeLink } from "./router";
import { sortAs } from "./sorting";

export function ZapisnyListSelector({
  children,
}: {
  children: React.ReactNode;
}) {
  let query = useContext(QueryContext);
  const cache = new CacheRequester();
  const studia = cache.get("get_studia");

  let items = [];

  let showPridatButton = false;

  if (studia) {
    for (const studium of studia) {
      const zapisneListy = cache.get("get_zapisne_listy", studium.studium_key);
      if (!zapisneListy) continue;

      items.push(...zapisneListy);

      if (
        !studium.koniec &&
        !zapisneListy.some((zl) => zl.akademicky_rok === currentAcademicYear())
      ) {
        showPridatButton = true;
      }
    }
  }

  items = sortBy(items, (item) => sortAs.date(item.datum_zapisu)).reverse();

  if (!query.zapisnyListKey && cache.loadedAll && items[0]) {
    const mostRecentItem = items[0];
    query = { ...query, zapisnyListKey: mostRecentItem.zapisny_list_key };
  }

  return (
    <React.Fragment>
      <ul className="nav nav-pills selector">
        <li>
          <span className="text-pill">Zápisný list:</span>
        </li>
        {items.map((zapisnyList, index) => {
          // An item's `index` might change over time as more get_zapisne_listy
          // responses arrive, but that should be harmless here.
          const zapisnyListKey = zapisnyList.zapisny_list_key;
          const active = zapisnyListKey == query.zapisnyListKey;
          return (
            <li key={index} className={active ? "active" : ""}>
              <RelativeLink href={{ zapisnyListKey }}>
                {zapisnyList.akademicky_rok} {zapisnyList.sp_skratka}
              </RelativeLink>
            </li>
          );
        })}
        {!cache.loadedAll ?
          <li>
            <span className="text-pill">
              <Loading requests={cache.missing} />
            </span>
          </li>
        : showPridatButton ?
          <li>
            <Link href={{ action: "prehladStudia" }}>Pridať...</Link>
          </li>
        : null}
      </ul>
      {query.zapisnyListKey ?
        <QueryContext.Provider value={query}>{children}</QueryContext.Provider>
      : cache.loadedAll && items.length == 0 ?
        <p>Žiadne zápisné listy.</p>
      : null}
    </React.Fragment>
  );
}
