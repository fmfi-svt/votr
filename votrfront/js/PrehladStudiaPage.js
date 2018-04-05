
import { CacheRequester, Loading } from './ajax';
import { PageLayout, PageTitle } from './layout';
import { sortAs, sortTable } from './sorting';


// TODO: Pridat kadejake sumarne informacie, aby to vyzeralo ako dashboard.
// TODO: Ked to raz bude rychle, pouzit to ako "home page" pri prazdnom action.
// TODO: Zvyraznit aktualne obdobia a pisat kolko casu zostava do dalsich.


export var PrehladStudiumColumns = [
  ["Študijný program", 'sp_popis'],
  ["Rok štúdia", 'rok_studia', sortAs.number],
  ["Dĺžka v semestroch", 'sp_dlzka', sortAs.number],
  ["Začiatok štúdia", 'zaciatok', sortAs.date],
  ["Koniec štúdia", 'koniec', sortAs.date],
  ["Doplňujúce údaje", 'sp_doplnujuce_udaje']
];
PrehladStudiumColumns.defaultOrder = 'd4';


export var PrehladZapisnyListColumns = [
  ["Akademický rok", 'akademicky_rok'],
  ["Študijný program", 'sp_popis'],
  ["Ročník", 'rocnik', sortAs.number],
  ["Dátum zápisu", 'datum_zapisu', sortAs.date]
];
PrehladZapisnyListColumns.defaultOrder = 'd0d3';


export var PrehladStudiaPage = createReactClass({
  propTypes: {
    query: PropTypes.object.isRequired
  },

  renderObdobie(label, rpcName, arg) {
    var cache = new CacheRequester();
    var result = cache.get(rpcName, arg);
    return <tr>
      <th>{label}</th>
      <td>
        {result ?
          result.obdobie_od + " \u2013 " + result.obdobie_do :
          <Loading requests={cache.missing} />}
      </td>
    </tr>;
  },

  renderObdobia() {
    // Obdobia predsalen neukazujeme, lebo AIS ma vacsinou zle informacie
    // (skuskove je umelo predlzene kvoli moznosti zapisovat znamky, apod) a
    // nechceme byt matuci. Zapnut sa daju tymto schovanym query flagom.
    if (!this.props.query.reallyShowDates) {
      return null;
    }

    return <table className="table table-narrow table-condensed table-bordered table-hover">
      <tbody>
        {this.renderObdobie("Zimný semester", 'get_semester_obdobie', 'Z')}
        {this.renderObdobie("Zimné skúškové", 'get_skuskove_obdobie', 'Z')}
        {this.renderObdobie("Letný semester", 'get_semester_obdobie', 'L')}
        {this.renderObdobie("Letné skúškové", 'get_skuskove_obdobie', 'L')}
      </tbody>
    </table>;
  },

  renderStudia() {
    var cache = new CacheRequester();

    var studia = cache.get('get_studia');

    if (!studia) {
      return <Loading requests={cache.missing} />;
    }

    var [studia, header] = sortTable(
      studia, PrehladStudiumColumns, this.props.query, 'studiaSort');

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
          </tr>
        )}
      </tbody>
      {message && <tfoot><tr><td colSpan={PrehladStudiumColumns.length}>{message}</td></tr></tfoot>}
    </table>;
  },

  renderZapisneListy() {
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
      this.props.query, 'zapisneListySort');

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
  },

  render() {
    return <PageLayout query={this.props.query}>
      <div className="header">
        <PageTitle>Prehľad štúdia</PageTitle>
      </div>
      {this.renderObdobia()}
      <h2>Zoznam štúdií</h2>
      {this.renderStudia()}
      <h2>Zoznam zápisných listov</h2>
      {this.renderZapisneListy()}
    </PageLayout>;
  }
});
