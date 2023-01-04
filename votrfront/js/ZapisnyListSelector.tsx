import React, { useContext } from "react";
import _ from "lodash";
import { CacheRequester, Loading } from "./ajax";
import { Link, QueryContext, RelativeLink } from "./router";
import { sortAs } from "./sorting";
import { currentAcademicYear } from "./coursesStats";
import { ZapisnyList } from "./types";

function getItems(cache: CacheRequester): [ZapisnyList[], boolean] {
  var studia = cache.get("get_studia");

  var items = [];

  var buttonNovyZapisnyList = false;

  if (studia) {
    for (const studium of studia) {
      var zapisneListy = cache.get("get_zapisne_listy", studium.studium_key);
      if (zapisneListy) items.push(...zapisneListy);

      var aktualny = 0;
      if (zapisneListy !== null) {
        aktualny = zapisneListy.filter(
          (zl) => zl.akademicky_rok === currentAcademicYear()
        ).length;
      }
      if (studium.koniec === "" && aktualny === 0) {
        buttonNovyZapisnyList = true;
      }
    }
  }

  return [
    _.sortBy(items, (item) => sortAs.date(item.datum_zapisu)).reverse(),
    buttonNovyZapisnyList,
  ];
}

export function ZapisnyListSelector(props: { children: React.ReactNode }) {
  var query = useContext(QueryContext);
  var cache = new CacheRequester();
  var [items, buttonNovyZapisnyList] = getItems(cache);

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
        {cache.loadedAll ? null : (
          <li>
            <span className="text-pill">
              <Loading requests={cache.missing} />
            </span>
          </li>
        )}
        {buttonNovyZapisnyList && (
          <li>
            <Link href={{ action: "prehladStudia" }}>Pridať...</Link>
          </li>
        )}
      </ul>
      {query.zapisnyListKey ? (
        <QueryContext.Provider value={query}>
          {props.children}
        </QueryContext.Provider>
      ) : cache.loadedAll && items.length == 0 ? (
        <p>Žiadne zápisné listy.</p>
      ) : null}
    </React.Fragment>
  );
}
