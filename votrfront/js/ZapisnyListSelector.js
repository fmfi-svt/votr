
import { CacheRequester, Loading } from './ajax';
import { Link, QueryContext, queryConsumer } from './router';
import { sortAs } from './sorting';
import { currentAcademicYear } from './coursesStats';

var buttonNovyZapisnyList = false;

function getItems(cache) {
  var studia = cache.get('get_studia');

  var items = [];

  buttonNovyZapisnyList = false;
    
  if (studia) studia.forEach((studium) => {
    var zapisneListy = cache.get('get_zapisne_listy', studium.studium_key);
    if (zapisneListy) items.push(...zapisneListy);
   
    var aktualny = 0;
    if (zapisneListy !== null) {
        aktualny = zapisneListy.filter(zl => zl.akademicky_rok === currentAcademicYear()).length;
    }
    if (studium.koniec === '' && aktualny === 0) {
        buttonNovyZapisnyList = true;
    }
  });

  return _.sortBy(items, (item) => sortAs.date(item.datum_zapisu)).reverse();
}


export function ZapisnyListSelector(props) {
  return queryConsumer(query => {
    var cache = new CacheRequester();
    var items = getItems(cache);

    if (!query.zapisnyListKey && cache.loadedAll && items.length) {
      var mostRecentItem = items[0];
      query = { ...query, zapisnyListKey: mostRecentItem.zapisny_list_key };
    }

    return (
      <React.Fragment>
        <ul className="nav nav-pills selector">
          <li><span className="text-pill">Zápisný list:</span></li>
          {items.map((zapisnyList) => {
            var key = zapisnyList.zapisny_list_key;
            var active = key == query.zapisnyListKey;
            return <li key={key} className={active ? "active" : ""}>
              <Link href={{ ...query, zapisnyListKey: key }}>
                {zapisnyList.akademicky_rok} {zapisnyList.sp_skratka}
              </Link>
            </li>;
          })}
          {cache.loadedAll ? null :
            <li><span className="text-pill">
              <Loading requests={cache.missing} />
            </span></li>}
          {buttonNovyZapisnyList &&
           <li><Link href={{ action: 'prehladStudia' }}>Pridať...</Link></li>
          }
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
  });
}
