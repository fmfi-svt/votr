/** @jsx React.DOM */

(function () {


var TYPY_VYUCBY = {
  'A': 'A - povinné',
  'B': 'B - povinne voliteľné',
  'C': 'C - výberové'
};


// TODO: Sorting
// TODO: Pocet predmetov, sucet kreditov
// TODO: Neoficialne priemery ala fajr

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

    return <table>
      <thead>
        <tr>
          <th>Akademický rok</th>
          <th>Semester</th>
          <th>Skratka</th>
          <th>Názov predmetu</th>
          <th>Kredit</th>
          <th>Typ výučby</th>
          <th>Hodnotenie</th>
          <th>Dátum hodnotenia</th>
          <th>Termín hodnotenia</th>
        </tr>
      </thead>
      <tbody>
        {hodnotenia.map((hodnotenie) =>
          <tr key={hodnotenie.key} className={hodnotenie.semester == 'Z' ? 'zima' : 'leto'}>
            <td>{hodnotenie.akademicky_rok}</td>
            <td>{hodnotenie.semester}</td>
            <td>{hodnotenie.skratka}</td>
            <td>{hodnotenie.nazov}</td>
            <td>{hodnotenie.kredit}</td>
            <td>{TYPY_VYUCBY[hodnotenie.typ_vyucby] || hodnotenie.typ_vyucby}</td>
            <td>
              {hodnotenie.hodn_znamka}
              {hodnotenie.hodn_znamka ? " - " : null}
              {hodnotenie.hodn_znamka_popis}
            </td>
            <td>{hodnotenie.hodn_datum}</td>
            <td>{hodnotenie.hodn_termin}</td>
          </tr>
        )}
      </tbody>
    </table>;
  },

  renderPriemery: function () {
    var cache = new Votr.CacheRequester();
    var {studiumKey} = this.props.query;

    var priemery;
    var zapisneListy = cache.get('get_zapisne_listy', studiumKey);

    if (zapisneListy) {
      var zapisnyListKey = _.max(zapisneListy,
          (zapisnyList) => dateToInteger(zapisnyList.datum_zapisu)).key;
      priemery = cache.get('get_priemery', studiumKey, zapisnyListKey);
    } else if (zapisneListy === []) {
      priemery = [];
    }

    if (priemery === undefined) {
      return <Votr.Loading requests={cache.missing} />;
    }

    return <table>
      <thead>
        <tr>
          <th>Akademický rok</th>
          <th>Názov priemeru</th>
          <th>Semester</th>
          <th>Získaný kredit</th>
          <th>Celkový počet predmetov</th>
          <th>Počet neabsolvovaných predmetov</th>
          <th>Študijný priemer</th>
          <th>Vážený priemer</th>
          <th>Priemer na koľký pokus</th>
          <th>Dátum výpočtu priemeru</th>
        </tr>
      </thead>
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
