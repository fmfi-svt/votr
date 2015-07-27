(function () {


Votr.MojeHodnoteniaColumns = [
  ["Akademický rok", 'akademicky_rok']
].concat(Votr.MojePredmetyColumns);
Votr.MojeHodnoteniaColumns.defaultOrder = 'a0d1a2';


Votr.MojePriemeryColumns = [
  ["Dátum výpočtu priemeru", 'datum_vypoctu', Votr.sortAs.date],
  ["Názov priemeru", 'nazov'],
  ["Akademický rok", 'akademicky_rok'],
  ["Semester", 'semester', null, true],
  ["Získaný kredit", 'ziskany_kredit', Votr.sortAs.number],
  ["Celkový počet predmetov", 'predmetov', Votr.sortAs.number],
  ["Počet neabsolvovaných predmetov", 'neabsolvovanych', Votr.sortAs.number],
  ["Študijný priemer", 'studijny_priemer', Votr.sortAs.number],
  ["Vážený priemer", 'vazeny_priemer', Votr.sortAs.number]
];
Votr.MojePriemeryColumns.defaultOrder = 'a0a2a1';


Votr.MojeHodnoteniaPageContent = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  renderHodnotenia: function () {
    var cache = new Votr.CacheRequester();
    var {studiumKey} = this.props.query;
    var [hodnotenia, message] = cache.get('get_prehlad_kreditov', studiumKey) || [];

    if (!hodnotenia) {
      return <Votr.Loading requests={cache.missing} />;
    }

    var [hodnotenia, header] = Votr.sortTable(
      hodnotenia, Votr.MojeHodnoteniaColumns, this.props.query, 'predmetySort');

    var stats = Votr.coursesStats(hodnotenia);

    return <table className="table table-condensed table-bordered table-striped table-hover">
      <thead>{header}</thead>
      <tbody>
        {hodnotenia.map((hodnotenie) =>
          <tr key={hodnotenie.hodn_key} className={Votr.classForSemester(hodnotenie.semester)}>
            <td>{hodnotenie.akademicky_rok}</td>
            <td>{hodnotenie.semester}</td>
            <td><Votr.Link href={_.assign({}, this.props.query, { modal: 'detailPredmetu', modalPredmetKey: hodnotenie.predmet_key, modalAkademickyRok: hodnotenie.akademicky_rok })}>
              {hodnotenie.nazov}
            </Votr.Link></td>
            <td>{hodnotenie.skratka}</td>
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
            <td colSpan="4">Celkom {stats.spolu.count} {Votr.plural(stats.spolu.count, "predmet", "predmety", "predmetov")}</td>
            <td>{stats.spolu.creditsCount}</td>
            <td></td>
            <td>{Votr.renderWeightedStudyAverage(hodnotenia)}</td>
            <td></td>
            <td></td>
          </tr>
          {message && <tr><td colSpan={Votr.MojeHodnoteniaColumns.length}>{message}</td></tr>}
      </tfoot>
    </table>;
  },

  renderPriemery: function () {
    var cache = new Votr.CacheRequester();
    var {studiumKey} = this.props.query;

    var priemery, message;
    var zapisneListy = cache.get('get_zapisne_listy', studiumKey);

    if (zapisneListy && zapisneListy.length == 0) {
      priemery = [];
    } else if (zapisneListy) {
      var zapisnyListKey = _.max(zapisneListy,
          (zapisnyList) => Votr.sortAs.date(zapisnyList.datum_zapisu)).zapisny_list_key;
      [priemery, message] = cache.get('get_priemery', zapisnyListKey) || [];
    }

    if (!priemery) {
      return <Votr.Loading requests={cache.missing} />;
    }

    var [priemery, header] = Votr.sortTable(
      priemery, Votr.MojePriemeryColumns, this.props.query, 'priemerySort');

    if (!message && !priemery.length) {
      message = "V AISe zatiaľ nie sú vypočítané žiadne priemery.";
    }

    return <table className="table table-condensed table-bordered table-striped table-hover">
      <thead>{header}</thead>
      <tbody>
        {priemery.map((priemer, index) =>
          <tr key={index}>
            <td>{priemer.datum_vypoctu}</td>
            <td>{Votr.humanizeNazovPriemeru(priemer.nazov)}</td>
            <td>{priemer.akademicky_rok}</td>
            <td>{priemer.semester}</td>
            <td>{priemer.ziskany_kredit}</td>
            <td>{priemer.predmetov}</td>
            <td>{priemer.neabsolvovanych}</td>
            <td>{priemer.studijny_priemer}</td>
            <td>{priemer.vazeny_priemer}</td>
          </tr>
        )}
      </tbody>
      {message && <tfoot><tr><td colSpan={Votr.MojePriemeryColumns.length}>{message}</td></tr></tfoot>}
    </table>;
  },

  render: function () {
    return <div>
      <div className="header">
        <Votr.PageTitle>Moje hodnotenia</Votr.PageTitle>
      </div>
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
