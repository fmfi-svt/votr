/** @jsx React.DOM */

(function () {


// TODO: Pridat kadejake sumarne informacie, aby to vyzeralo ako dashboard.
// TODO: Ked to raz bude rychle, pouzit to ako "home page" pri prazdnom action.
// TODO: Zvyraznit aktualne obdobia a pisat kolko casu zostava do dalsich.


Votr.PrehladStudiumColumns = [
  ["Študijný program", 'sp_popis'],
  ["Rok štúdia", 'rok_studia', Votr.sortAs.number],
  ["Dĺžka v semestroch", 'sp_dlzka', Votr.sortAs.number],
  ["Začiatok štúdia", 'zaciatok', Votr.sortAs.date],
  ["Koniec štúdia", 'koniec', Votr.sortAs.date],
  ["Doplňujúce údaje", 'sp_doplnujuce_udaje']
];
Votr.PrehladStudiumColumns.defaultOrder = 'd4';


Votr.PrehladZapisnyListColumns = [
  ["Akademický rok", 'akademicky_rok'],
  ["Študijný program", 'sp_popis'],
  ["Ročník", 'rocnik', Votr.sortAs.number],
  ["Dátum zápisu", 'datum_zapisu', Votr.sortAs.date]
];
Votr.PrehladZapisnyListColumns.defaultOrder = 'd0d3';


Votr.PrehladStudiaPage = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  renderObdobie: function (label, rpcName, arg) {
    var cache = new Votr.CacheRequester();
    var result = cache.get(rpcName, arg);
    return <tr>
      <th>{label}</th>
      <td>
        {result ?
          result.obdobie_od + " \u2013 " + result.obdobie_do :
          <Votr.Loading requests={cache.missing} />}
      </td>
    </tr>;
  },

  renderObdobia: function () {
    return <table className="table table-narrow table-condensed table-bordered table-hover">
      <tbody>
        {this.renderObdobie("Zimný semester", 'get_semester_obdobie', 'Z')}
        {this.renderObdobie("Zimné skúškové", 'get_skuskove_obdobie', 'Z')}
        {this.renderObdobie("Letný semester", 'get_semester_obdobie', 'L')}
        {this.renderObdobie("Letné skúškové", 'get_skuskove_obdobie', 'L')}
      </tbody>
    </table>;
  },

  renderStudia: function () {
    var cache = new Votr.CacheRequester();

    var studia = cache.get('get_studia');

    if (!studia) {
      return <Votr.Loading requests={cache.missing} />;
    }

    var [studia, header] = Votr.sortTable(
      studia, Votr.PrehladStudiumColumns, this.props.query, 'studiaSort');

    return <table className="table table-condensed table-bordered table-striped table-hover">
      <thead>{header}</thead>
      <tbody>
        {studia.map((studium) =>
          <tr key={studium.key}>
            <td>{studium.sp_popis} ({studium.sp_skratka})</td>
            <td>{studium.rok_studia}</td>
            <td>{studium.sp_dlzka}</td>
            <td>{studium.zaciatok}</td>
            <td>{studium.koniec}</td>
            <td>{studium.sp_doplnujuce_udaje.replace(/^\((.*)\)$/, '$1')}</td>
          </tr>
        )}
      </tbody>
    </table>;
  },

  renderZapisneListy: function () {
    var cache = new Votr.CacheRequester();

    var studia = cache.get('get_studia');

    if (!studia) {
      return <Votr.Loading requests={cache.missing} />;
    }

    var zapisneListy = [];

    if (studia) studia.forEach((studium) => {
      var mojeZapisneListy = cache.get('get_zapisne_listy', studium.key);
      if (mojeZapisneListy) mojeZapisneListy.forEach((zapisnyList) => {
        zapisneListy.push(zapisnyList);
      });
    });

    var [zapisneListy, header] = Votr.sortTable(
      zapisneListy, Votr.PrehladZapisnyListColumns,
      this.props.query, 'zapisneListySort');

    var showTable = zapisneListy.length || cache.loadedAll;

    return <span>
      {!cache.loadedAll && <Votr.Loading requests={cache.missing} />}
      {showTable &&
        <table className="table table-condensed table-bordered table-striped table-hover">
          <thead>{header}</thead>
          <tbody>
            {zapisneListy.map((zapisnyList, index) =>
              <tr key={index}>
                <td>{zapisnyList.akademicky_rok}</td>
                <td>{zapisnyList.sp_popis} ({zapisnyList.sp_skratka})</td>
                <td>{zapisnyList.rocnik}</td>
                <td>{zapisnyList.datum_zapisu}</td>
              </tr>
            )}
          </tbody>
        </table>}
    </span>;
  },

  render: function () {
    return <Votr.PageLayout query={this.props.query}>
      <Votr.PageTitle>Prehľad štúdia</Votr.PageTitle>
      {this.renderObdobia()}
      <h2>Zoznam štúdií</h2>
      {this.renderStudia()}
      <h2>Zoznam zápisných listov</h2>
      {this.renderZapisneListy()}
    </Votr.PageLayout>;
  }
});


})();
