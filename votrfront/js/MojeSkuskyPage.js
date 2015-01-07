(function () {


// TODO: Oddelit Aktualne terminy hodnotenia vs Stare terminy hodnotenia

Votr.MojeSkuskyColumns = [
  ["Moje?", null, (termin) => !termin.datum_prihlasenia || termin.datum_odhlasenia ? 'N' : 'A'],
  ["Predmet", 'nazov_predmetu'],
  ["Dátum", 'datum', Votr.sortAs.date],
  ["Čas", 'cas'],
  ["Miestnosť", 'miestnost'],
  ["Hodnotiaci", 'hodnotiaci', Votr.sortAs.personName],
  ["Prihlásení", 'pocet_prihlasenych', Votr.sortAs.number],
  ["Poznámka", 'poznamka'],
  ["Prihlasovanie", 'prihlasovanie', Votr.sortAs.interval],
  ["Odhlasovanie", 'odhlasovanie', Votr.sortAs.interval],
  ["Známka", null, (termin) => termin.hodnotenie_terminu || termin.hodnotenie_predmetu]
];


Votr.MojeSkuskyPageContent = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  renderContent: function () {
    var cache = new Votr.CacheRequester();
    var {studiumKey, zapisnyListKey} = this.props.query;

    var vidim = cache.get('get_vidim_terminy_hodnotenia', studiumKey, zapisnyListKey);

    if (!cache.loadedAll) {
      return <Votr.Loading requests={cache.missing} />;
    }

    if (!vidim) {
      return <p>Skúšky pre tento zápisný list už nie sú k dispozícii.</p>;
    }

    var terminyPrihlasene = cache.get('get_prihlasene_terminy', studiumKey, zapisnyListKey);
    var terminyVypisane = cache.get('get_vypisane_terminy', studiumKey, zapisnyListKey);

    if (!terminyPrihlasene || !terminyVypisane) {
      return <Votr.Loading requests={cache.missing} />;
    }

    var terminy = {};
    terminyVypisane.forEach((termin) => terminy[termin.key] = termin);
    terminyPrihlasene.forEach((termin) => terminy[termin.key] = termin);
    terminy = _.values(terminy);

    var [terminy, header] = Votr.sortTable(
      terminy, Votr.MojeSkuskyColumns, this.props.query, 'skuskySort');

    var message = terminy.length ? null : "Zatiaľ nie sú vypísané žiadne termíny.";

    return <table className="table table-condensed table-bordered table-striped table-hover with-buttons-table">
      <thead>{header}</thead>
      <tbody>
        {terminy.map((termin) =>
          <tr key={termin.key}>
            {!termin.datum_prihlasenia || termin.datum_odhlasenia ?
              <td title="Nie ste prihlásení" className="text-center text-negative">{"\u2718"}</td> :
              <td title="Ste prihlásení" className="text-center text-positive">{"\u2714"}</td> }
            <td><Votr.Link href={_.assign({}, this.props.query, { modal: 'detailPredmetu', modalPredmetKey: termin.predmet_key, modalAkademickyRok: termin.akademicky_rok })}>
              {termin.nazov_predmetu}
            </Votr.Link></td>
            <td>{termin.datum}</td>
            <td>{termin.cas}</td>
            <td>{termin.miestnost}</td>
            <td>{termin.hodnotiaci}</td>
            <td><Votr.Link href={_.assign({}, this.props.query, { modal: 'zoznamPrihlasenychNaTermin', modalStudiumKey: studiumKey, modalZapisnyListKey: zapisnyListKey, modalPredmetKey: termin.predmet_key, modalTerminKey: termin.key })}>
              {termin.pocet_prihlasenych +
               (termin.maximalne_prihlasenych ? "/" + termin.maximalne_prihlasenych : "")}
            </Votr.Link></td>
            <td>{termin.poznamka}</td>
            <td>{termin.prihlasovanie}</td>
            <td>{termin.odhlasovanie}</td>
            <td>
              {termin.hodnotenie_terminu ? termin.hodnotenie_terminu :
               termin.hodnotenie_predmetu ? termin.hodnotenie_predmetu + ' (nepriradená k termínu)' :
               null}
               <Votr.SkuskyRegisterButton studiumKey={studiumKey} zapisnyListKey={zapisnyListKey} termin={termin}/>
            </td>
          </tr>
        )}
      </tbody>
      {message && <tfoot><tr><td colSpan={Votr.MojeSkuskyColumns.length}>{message}</td></tr></tfoot>}
    </table>;
  },

  render: function () {
    return <div>
      <Votr.PageTitle>Moje skúšky</Votr.PageTitle>
      {this.renderContent()}
    </div>;
  }
});


Votr.SkuskyRegisterButton = React.createClass({
  propTypes: {
    studiumKey: React.PropTypes.string.isRequired,
    zapisnyListKey: React.PropTypes.string.isRequired,
    termin: React.PropTypes.object.isRequired
  },

  getInitialState: function () {
    return {
      pressed: false
    };
  },

  handleClick: function() {
    var command = this.isSigninButton() ? 'prihlas_na_termin' : 'odhlas_z_terminu';
    var {studiumKey, zapisnyListKey, termin} = this.props;

    Votr.sendRpc(command, [studiumKey, zapisnyListKey, termin.predmet_key, termin.key], (message) => {
      if (message) {
        this.setState({ pressed: false });
        alert(message);
      } else {
        Votr.RequestCache.invalidate('get_prihlasene_terminy');
        Votr.RequestCache.invalidate('get_vypisane_terminy');
        Votr.RequestCache.invalidate('get_prihlaseni_studenti');
      }
    });

    this.setState({ pressed: true });
  },

  isDisabled: function() {
    var termin = this.props.termin;
    return (this.isSigninButton() && termin.moznost_prihlasit !== 'A') || this.state.pressed;
  },

  isSigninButton: function() {
    var termin = this.props.termin;
    return !termin.datum_prihlasenia || termin.datum_odhlasenia;
  },

  render: function () {
    var termin = this.props.termin;

    if (termin.hodnotenie_terminu || termin.hodnotenie_predmetu) {
      return null;
    }

    var today = new Date().toJSON().replace(/-/g, '').substring(0, 8);
    if (today > Votr.sortAs.date(termin.datum)) return null;

    var buttonClass = "btn btn-xs " + (this.isSigninButton() ? "btn-success" : "btn-danger") + (this.isDisabled() ? " appear-disabled" : "");
    var buttonText = this.state.pressed ? <Votr.Loading /> : this.isSigninButton() ? "Prihlásiť" : "Odhlásiť";

    return <button onClick={this.state.pressed ? null : this.handleClick} className={buttonClass}>{buttonText}</button>;
  }
});


Votr.MojeSkuskyPage = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  render: function () {
    return <Votr.PageLayout query={this.props.query}>
      <Votr.ZapisnyListSelector query={this.props.query} component={Votr.MojeSkuskyPageContent} />
    </Votr.PageLayout>;
  }
});


})();
