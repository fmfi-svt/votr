/** @jsx React.DOM */

(function () {


Votr.MojeHodnoteniaColumns = [
  ["Akademický rok", 'akademicky_rok']
].concat(Votr.MojePredmetyColumns);
Votr.MojeHodnoteniaColumns.defaultOrder = 'a0d1a3';


Votr.MojePriemeryColumns = [
  ["Akademický rok", 'akademicky_rok'],
  ["Názov priemeru", 'nazov'],
  ["Semester", 'semester', null, true],
  ["Získaný kredit", 'ziskany_kredit', Votr.sortAs.number],
  ["Celkový počet predmetov", 'predmetov', Votr.sortAs.number],
  ["Počet neabsolvovaných predmetov", 'neabsolvovanych', Votr.sortAs.number],
  ["Študijný priemer", 'studijny_priemer', Votr.sortAs.number],
  ["Vážený priemer", 'vazeny_priemer', Votr.sortAs.number],
  ["Priemer na koľký pokus", 'pokusy_priemer', Votr.sortAs.number],
  ["Dátum výpočtu priemeru", 'datum_vypoctu', Votr.sortAs.date]
];
Votr.MojePriemeryColumns.defaultOrder = 'a9a0a1';


Votr.MojeHodnoteniaPageContent = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  renderHodnotenia: function () {
    var cache = new Votr.CacheRequester();
    var {studiumKey} = this.props.query;
    var hodnotenia = cache.get('get_prehlad_kreditov', studiumKey);

    if (!hodnotenia) {
      return <Votr.Loading requests={cache.missing} />;
    }

    var [hodnotenia, header] = Votr.sortTable(
      hodnotenia, Votr.MojeHodnoteniaColumns, this.props.query, 'predmetySort');

    var coursesStats = Votr.coursesStats(hodnotenia);

    return <table className="table table-condensed table-bordered table-striped table-hover">
      <thead>{header}</thead>
      <tbody>
        {hodnotenia.map((hodnotenie) =>
          <tr key={hodnotenie.key} className={hodnotenie.semester == 'Z' ? 'zima' : 'leto'}>
            <td>{hodnotenie.akademicky_rok}</td>
            <td>{hodnotenie.semester}</td>
            <td>{hodnotenie.skratka}</td>
            <td><Votr.Link href={_.assign({}, this.props.query, { modal: 'detailPredmetu', modalPredmetKey: hodnotenie.key, modalAkademickyRok: hodnotenie.akademicky_rok })}>
              {hodnotenie.nazov}
            </Votr.Link></td>
            <td>{hodnotenie.kredit}</td>
            <td>{Votr.humanizeTypVyucby(hodnotenie.typ_vyucby)}</td>
            <td>
              {hodnotenie.hodn_znamka}
              {hodnotenie.hodn_znamka ? " - " : null}
              {hodnotenie.hodn_znamka_popis}
            </td>
            <td>{hodnotenie.hodn_datum}</td>
            <td>{Votr.humanizeTerminHodnotenia(hodnotenie.hodn_termin)}</td>
          </tr>
        )}
      </tbody>
      <tfoot>
          <tr>
            <td colSpan="4">Celkom {coursesStats.spolu.count} predmetov</td>
            <td>{coursesStats.spolu.creditsCount}</td>
            <td></td>
            <td>{Votr.renderWeightedStudyAverage(hodnotenia)}</td>
            <td></td>
            <td></td>
          </tr>
      </tfoot>
    </table>;
  },

  renderPriemery: function () {
    var cache = new Votr.CacheRequester();
    var {studiumKey} = this.props.query;

    var priemery;
    var zapisneListy = cache.get('get_zapisne_listy', studiumKey);

    if (zapisneListy) {
      var zapisnyListKey = _.max(zapisneListy,
          (zapisnyList) => Votr.sortAs.date(zapisnyList.datum_zapisu)).key;
      priemery = cache.get('get_priemery', studiumKey, zapisnyListKey);
    } else if (zapisneListy === []) {
      priemery = [];
    }

    if (!priemery && priemery !== []) {
      return <Votr.Loading requests={cache.missing} />;
    }

    var [priemery, header] = Votr.sortTable(
      priemery, Votr.MojePriemeryColumns, this.props.query, 'priemerySort');

    return <table className="table table-condensed table-bordered table-striped table-hover">
      <thead>{header}</thead>
      <tbody>
        {priemery.map((priemer, index) =>
          <tr key={index}>
            <td>{priemer.akademicky_rok}</td>
            <td>{priemer.nazov}</td>
            <td>{priemer.semester}</td>
            <td>{priemer.ziskany_kredit}</td>
            <td>{priemer.predmetov}</td>
            <td>{priemer.neabsolvovanych}</td>
            <td>{priemer.studijny_priemer}</td>
            <td>{priemer.vazeny_priemer}</td>
            <td>{priemer.pokusy_priemer}</td>
            <td>{priemer.datum_vypoctu}</td>
          </tr>
        )}
      </tbody>
    </table>;
  },

  render: function () {
    return <div>
      <Votr.PageTitle>Moje hodnotenia</Votr.PageTitle>
      {this.renderHodnotenia()}
      <h2>Moje priemery</h2>
      {this.renderPriemery()}
    </div>;
  }
});


Votr.MojeHodnoteniaPage = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  render: function () {
    return <Votr.PageLayout query={this.props.query}>
      <Votr.StudiumSelector query={this.props.query} component={Votr.MojeHodnoteniaPageContent} />
    </Votr.PageLayout>;
  }
});


})();
