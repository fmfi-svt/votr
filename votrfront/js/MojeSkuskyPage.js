
import { ZapisnyListSelector } from './ZapisnyListSelector';
import { CacheRequester, Loading, RequestCache, sendRpc } from './ajax';
import { PageLayout, PageTitle } from './layout';
import { Link } from './router';
import { sortAs, sortTable } from './sorting';

export var MojeSkuskyColumns = [
  ["Moje?", null, (termin) => !termin.datum_prihlasenia || termin.datum_odhlasenia ? 'N' : 'A'],
  ["Predmet", 'nazov_predmetu'],
  ["Dátum", 'datum', sortAs.date],
  ["Miestnosť", 'miestnost'],
  ["Hodnotiaci", 'hodnotiaci', sortAs.personName],
  ["Prihlásení", 'pocet_prihlasenych', sortAs.number],
  ["Poznámka", 'poznamka'],
  ["Prihlasovanie", 'prihlasovanie', sortAs.interval],
  ["Odhlasovanie", 'odhlasovanie', sortAs.interval],
  ["Známka", null, (termin) => termin.hodnotenie_terminu || termin.hodnotenie_predmetu]
];


export var MojeSkuskyPageContent = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  getInitialState() {
    // v state.predmety je uložené, či zobraziť skúšky pre každý predmet
    return {
      predmety: {}
    };
  },

  renderContent() {
    var cache = new CacheRequester();
    var {zapisnyListKey} = this.props.query;

    var vidim = cache.get('get_vidim_terminy_hodnotenia', zapisnyListKey);

    if (!cache.loadedAll) {
      return <Loading requests={cache.missing} />;
    }

    if (!vidim) {
      return <p>Skúšky pre tento zápisný list už nie sú k dispozícii.</p>;
    }

    var terminyPrihlasene = cache.get('get_prihlasene_terminy', zapisnyListKey);
    var terminyVypisane = cache.get('get_vypisane_terminy', zapisnyListKey);

    if (!terminyPrihlasene || !terminyVypisane) {
      return <Loading requests={cache.missing} />;
    }

    var terminy = {};
    terminyVypisane.forEach((termin) => terminy[termin.termin_key] = termin);
    terminyPrihlasene.forEach((termin) => terminy[termin.termin_key] = termin);
    terminy = _.values(terminy);

    var [terminy, header] = sortTable(
      terminy, MojeSkuskyColumns, this.props.query, 'skuskySort'
    );

    var message = terminy.length ? null : "Zatiaľ nie sú vypísané žiadne termíny.";

    var skuskyFiltrovane = {};
    var zobrazenePredmety = {};
    terminy.forEach(
      (termin) => {
        if (!skuskyFiltrovane[termin.nazov_predmetu]) {
          skuskyFiltrovane[termin.nazov_predmetu] = [];
          zobrazenePredmety[termin.nazov_predmetu] = false;
        }
        skuskyFiltrovane[termin.nazov_predmetu].push(termin);
      }
    );

    if (_.isEmpty(this.state.predmety)) {
      this.setState({predmety: zobrazenePredmety});
    }

    return (<div>
      {Object.keys(skuskyFiltrovane).sort().map((predmet) => 
        <div>
          <button
            type="button"
            className="btn btn-primary"
            style={{marginBottom: '5px', width: '300px'}}
            onClick={(e) => {
              e.preventDefault();
              this.setState({
                predmety: {
                  ...this.state.predmety,
                  [predmet]: !this.state.predmety[predmet],
                }
              });
            }}
          >{predmet}<span className="caret pull-right" style={{marginTop: '7px'}} /></button>
          {this.state.predmety[predmet] &&
            <table className="table table-condensed table-bordered table-striped table-hover with-buttons-table">
              <thead>{header}</thead>
              <tbody>
                {skuskyFiltrovane[predmet].map((termin) => this.renderTermin(termin))}
              </tbody>
            </table>
          }
        </div>
      )}
    </div>);
  },

  renderTermin(termin) {
    var today = new Date().toJSON().replace(/-/g, '').substring(0, 8);
    var farbaRiadku;
    
    if (today > sortAs.date(termin.datum)) {
      if (termin.hodnotenie_predmetu) {
        farbaRiadku = termin.hodnotenie_predmetu.includes('F') ? 'danger' : 'success';
      } else {
        farbaRiadku = 'info';
      }
    };

    var terminSkusky = termin.datum.split('.');
    var den = [
      'Nedeľa',
      'Pondelok',
      'Utorok',
      'Streda',
      'Štvrtok',
      'Piatok',
      'Sobota',
    ][new Date(terminSkusky[2], terminSkusky[1] - 1, terminSkusky[0]).getDay()];
    
    return (
      <tr key={termin.termin_key} className={farbaRiadku}>
        {!termin.datum_prihlasenia || termin.datum_odhlasenia ?
          <td title="Nie ste prihlásení" className="text-center text-negative">{"\u2718"}</td> :
          <td title="Ste prihlásení" className="text-center text-positive">{"\u2714"}</td> }
        <td>
          <Link href={{
            ...this.props.query,
            modal: 'detailPredmetu',
            modalPredmetKey: termin.predmet_key,
            modalAkademickyRok: termin.akademicky_rok
          }}>{termin.nazov_predmetu}</Link>
        </td>
        <td>{`${den} ${termin.datum} ${termin.cas}`}</td>
        <td>{termin.miestnost}</td>
        <td>{termin.hodnotiaci}</td>
        <td>
          <Link href={{...this.props.query, modal: 'zoznamPrihlasenychNaTermin', modalTerminKey: termin.termin_key}}>
            {termin.pocet_prihlasenych + (termin.maximalne_prihlasenych ? "/" + termin.maximalne_prihlasenych : "")}
          </Link>
        </td>
        <td>{termin.poznamka}</td>
        <td>{termin.prihlasovanie}</td>
        <td>{termin.odhlasovanie}</td>
        <td>
          {termin.hodnotenie_terminu ? termin.hodnotenie_terminu :
          termin.hodnotenie_predmetu ? termin.hodnotenie_predmetu + ' (nepriradená k termínu)' :
          null}
          <SkuskyRegisterButton termin={termin}/>
        </td>
      </tr>
    );
  },

  render() {
    return <div>
      <div className="header">
        <PageTitle>Moje skúšky</PageTitle>
      </div>
      {this.renderContent()}
    </div>;
  }
});


export var SkuskyRegisterButton = React.createClass({
  propTypes: {
    termin: React.PropTypes.object.isRequired
  },

  getInitialState() {
    return {
      pressed: false
    };
  },

  handleClick() {
    var command = this.isSigninButton() ? 'prihlas_na_termin' : 'odhlas_z_terminu';
    var termin = this.props.termin;

    sendRpc(command, [termin.termin_key], (message) => {
      if (message) {
        this.setState({ pressed: false });
        alert(message);
      } else {
        RequestCache.invalidate('get_prihlasene_terminy');
        RequestCache.invalidate('get_vypisane_terminy');
        RequestCache.invalidate('get_prihlaseni_studenti');
      }
    });

    this.setState({ pressed: true });
  },

  isDisabled() {
    var termin = this.props.termin;
    return (this.isSigninButton() && termin.moznost_prihlasit !== 'A') || this.state.pressed;
  },

  isSigninButton() {
    var termin = this.props.termin;
    return !termin.datum_prihlasenia || termin.datum_odhlasenia;
  },

  render() {
    var termin = this.props.termin;

    if (termin.hodnotenie_terminu) {
      return null;
    }

    var today = new Date().toJSON().replace(/-/g, '').substring(0, 8);
    if (today > sortAs.date(termin.datum)) return null;

    var buttonClass = "btn btn-xs " + (this.isSigninButton() ? "btn-success" : "btn-danger") + (this.isDisabled() ? " appear-disabled" : "");
    var buttonText = this.state.pressed ? <Loading /> : this.isSigninButton() ? "Prihlásiť" : "Odhlásiť";

    return <button onClick={this.state.pressed ? null : this.handleClick} className={buttonClass}>{buttonText}</button>;
  }
});


export var MojeSkuskyPage = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  render() {
    return <PageLayout query={this.props.query}>
      <ZapisnyListSelector query={this.props.query} component={MojeSkuskyPageContent} />
    </PageLayout>;
  }
});
