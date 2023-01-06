import _ from "lodash";
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
  var query = useContext(QueryContext);
  var cache = new CacheRequester();
  var studia = cache.get("get_studia");

  var items = [];

  var showPridatButton = false;

  if (studia) {
    for (const studium of studia) {
      var zapisneListy = cache.get("get_zapisne_listy", studium.studium_key);
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

  items = _.sortBy(items, (item) => sortAs.date(item.datum_zapisu)).reverse();

  if (!query.zapisnyListKey && cache.loadedAll && items[0]) {
    var mostRecentItem = items[0];
    query = { ...query, zapisnyListKey: mostRecentItem.zapisny_list_key };
  }

  return (
    <React.Fragment>
      <ul className="nav nav-pills selector">
        <li>
          <span className="text-pill">Zápisný list:</span>
        </li>
        {items.map((zapisnyList) => {
          var key = zapisnyList.zapisny_list_key;
          var active = key == query.zapisnyListKey;
          return (
            <li key={key} className={active ? "active" : ""}>
              <RelativeLink href={{ zapisnyListKey: key }}>
                {zapisnyList.akademicky_rok} {zapisnyList.sp_skratka}
              </RelativeLink>
            </li>
          );
        })}
        {!cache.loadedAll ? (
          <li>
            <span className="text-pill">
              <Loading requests={cache.missing} />
            </span>
          </li>
        ) : showPridatButton ? (
          <li>
            <Link href={{ action: "prehladStudia" }}>Pridať...</Link>
          </li>
        ) : null}
      </ul>
      {query.zapisnyListKey ? (
        <QueryContext.Provider value={query}>{children}</QueryContext.Provider>
      ) : cache.loadedAll && items.length == 0 ? (
        <p>Žiadne zápisné listy.</p>
      ) : null}
    </React.Fragment>
  );
}
