
import React from 'react';
import { CacheRequester, Loading, sendRpc, RequestCache } from './ajax';
import { PageLayout, PageTitle } from './layout';
import { queryConsumer } from './router';
import { sortAs, sortTable } from './sorting';
import { currentAcademicYear } from './coursesStats';


// TODO: Pridat kadejake sumarne informacie, aby to vyzeralo ako dashboard.
// TODO: Ked to raz bude rychle, pouzit to ako "home page" pri prazdnom action.
// TODO: Zvyraznit aktualne obdobia a pisat kolko casu zostava do dalsich.


export var PrehladStudiumColumns = [
  ["Študijný program", 'sp_popis'],
  ["Rok štúdia", 'rok_studia', sortAs.number],
  ["Dĺžka v semestroch", 'sp_dlzka', sortAs.number],
  ["Začiatok štúdia", 'zaciatok', sortAs.date],
  ["Koniec štúdia", 'koniec', sortAs.date],
  ["Doplňujúce údaje", 'sp_doplnujuce_udaje'],
  ["Zápisný list", 'zapisny_list']
];
PrehladStudiumColumns.defaultOrder = 'd4';


export var PrehladZapisnyListColumns = [
  ["Akademický rok", 'akademicky_rok'],
  ["Študijný program", 'sp_popis'],
  ["Ročník", 'rocnik', sortAs.number],
  ["Dátum zápisu", 'datum_zapisu', sortAs.date]
];
PrehladZapisnyListColumns.defaultOrder = 'd0d3';


export function PrehladStudiaObdobie(props) {
  var cache = new CacheRequester();
  var result = cache.get(props.rpc, props.semester);
  return (
    <tr>
      <th>{props.label}</th>
      <td>
        {result ?
          result.obdobie_od + " \u2013 " + result.obdobie_do :
          <Loading requests={cache.missing} />}
      </td>
    </tr>
  );
}


export function PrehladStudiaObdobia() {
  return queryConsumer(query => {
    // Obdobia predsalen neukazujeme, lebo AIS ma vacsinou zle informacie
    // (skuskove je umelo predlzene kvoli moznosti zapisovat znamky, apod) a
    // nechceme byt matuci. Zapnut sa daju tymto schovanym query flagom.
    if (!query.reallyShowDates) {
      return null;
    }

    return <table className="table table-narrow table-condensed table-bordered table-hover">
      <tbody>
        <PrehladStudiaObdobie label="Zimný semester" rpc="get_semester_obdobie" semester="Z" />
        <PrehladStudiaObdobie label="Zimné skúškové" rpc="get_skuskove_obdobie" semester="Z" />
        <PrehladStudiaObdobie label="Letný semester" rpc="get_semester_obdobie" semester="L" />
        <PrehladStudiaObdobie label="Letné skúškové" rpc="get_skuskove_obdobie" semester="L" />
      </tbody>
    </table>;
  });
}

function GetOficialnaDlzkaStudia(studium){

  // asi najlepsi test
  if (studium.sp_doplnujuce_udaje.includes("bakalársky")) return 3;
  if (studium.sp_doplnujuce_udaje.includes("magisterský")) return 2;

  // ak by bol nejaky preklep v skorsej informacii, pride dalsi test
  if (studium.sp_doplnujuce_udaje.includes("I. st.")) return 3;
  if (studium.sp_doplnujuce_udaje.includes("II. st.")) return 2;

  // a posledny
  if (studium.sp_skratka.charAt(0) == "m") return 2;
  else return 3;
}


export function PridatZapisnyListButton (props) {
    var studium = props.studium;
    var cache = new CacheRequester();
    var zapisne_listy = cache.get('get_zapisne_listy', studium.studium_key);
    var pocet_rokov_studovania = studium.rok_studia;
    var oficialna_dlzka_studia = GetOficialnaDlzkaStudia(studium);
    var rok_studia = pocet_rokov_studovania < oficialna_dlzka_studia ? pocet_rokov_studovania : oficialna_dlzka_studia;

    if (!cache.loadedAll) {
      return <Loading requests={cache.missing} />;
    }
        var aktualny_zapisny_list = 0;
        if (zapisne_listy !== null){
            aktualny_zapisny_list = zapisne_listy.filter(zl => zl.akademicky_rok === currentAcademicYear()).length;
        }
        if (studium.koniec === '') { // ak este neskoncilo studium
            if (aktualny_zapisny_list !== 0) { // ak uz mame zapisny list na tento rok
                return <button type="button" className='btn btn-xs btn-success' disabled={true}>Vytvoriť</button>
            } else { //  ak studium prebieha a nemame este zapisny list na tento rok
                return <button type="button" onClick={() => {
                    if (confirm(`Vytvoriť zápisný list pre akademický rok ${currentAcademicYear()}?`)) {
                            sendRpc('create_zapisny_list', [studium.studium_key, currentAcademicYear(), rok_studia],(message) =>
                                {if (message !== null) {alert(message);}
                                else {RequestCache.invalidate('get_zapisne_listy');}})}}}
                        className='btn btn-xs btn-success'>Vytvoriť</button>
            }
        } else { // ak studium uz skoncilo
            return null;
        }
}

export function PrehladStudiaStudia() {
  return queryConsumer(query => {
    var cache = new CacheRequester();

    var studia = cache.get('get_studia');

    if (!studia) {
      return <Loading requests={cache.missing} />;
    }

    var [studia, header] = sortTable(
      studia, PrehladStudiumColumns, query, 'studiaSort');

    var message = studia.length ? null : "V AISe nemáte žiadne štúdiá.";

    return <table className="table table-condensed table-bordered table-striped table-hover">
      <thead>{header}</thead>
      <tbody>
        {studia.map((studium) =>
          <tr key={studium.studium_key}>
            <td>{studium.sp_popis} ({studium.sp_skratka})</td>
            <td>{studium.rok_studia}</td>
            <td>{studium.sp_dlzka}</td>
            <td>{studium.zaciatok}</td>
            <td>{studium.koniec}</td>
            <td>{studium.sp_doplnujuce_udaje.replace(/^\((.*)\)$/, '$1')}</td>
            <td><PridatZapisnyListButton studium={studium} /></td>
          </tr>
        )}
      </tbody>
      {message && <tfoot><tr><td colSpan={PrehladStudiumColumns.length}>{message}</td></tr></tfoot>}
    </table>;
  });
}


export function PrehladStudiaZapisneListy() {
  return queryConsumer(query => {
    var cache = new CacheRequester();

    var studia = cache.get('get_studia');

    if (!studia) {
      return <Loading requests={cache.missing} />;
    }

    var zapisneListy = [];

    if (studia) studia.forEach((studium) => {
      var mojeZapisneListy = cache.get('get_zapisne_listy', studium.studium_key);
      if (mojeZapisneListy) mojeZapisneListy.forEach((zapisnyList) => {
        zapisneListy.push(zapisnyList);
      });
    });

    var [zapisneListy, header] = sortTable(
      zapisneListy, PrehladZapisnyListColumns,
      query, 'zapisneListySort');

    var showTable = zapisneListy.length || cache.loadedAll;

    var message = zapisneListy.length ? null : "V AISe nemáte žiadne zápisné listy.";

    return <React.Fragment>
      {!cache.loadedAll && <Loading requests={cache.missing} />}
      {showTable &&
        <table className="table table-condensed table-bordered table-striped table-hover">
          <thead>{header}</thead>
          <tbody>
            {zapisneListy.map((zapisnyList) =>
              <tr key={zapisnyList.zapisny_list_key}>
                <td>{zapisnyList.akademicky_rok}</td>
                <td>{zapisnyList.sp_popis} ({zapisnyList.sp_skratka})</td>
                <td>{zapisnyList.rocnik}</td>
                <td>{zapisnyList.datum_zapisu}</td>
              </tr>
            )}
          </tbody>
          {message && <tfoot><tr><td colSpan={PrehladZapisnyListColumns.length}>{message}</td></tr></tfoot>}
        </table>}
    </React.Fragment>;
  });
}


export function PrehladStudiaPage() {
  return (
    <PageLayout>
      <div className="header">
        <PageTitle>Prehľad štúdia</PageTitle>
      </div>
      <PrehladStudiaObdobia />
      <h2>Zoznam štúdií</h2>
      <PrehladStudiaStudia />
      <h2>Zoznam zápisných listov</h2>
      <PrehladStudiaZapisneListy />
    </PageLayout>
  );
}
