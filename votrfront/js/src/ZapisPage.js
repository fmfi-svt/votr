import React, { Component } from 'react';
import PropTypes from 'prop-types';

import { ZapisnyListSelector } from './ZapisnyListSelector';
import { CacheRequester, Loading, RequestCache, sendRpc } from './ajax';
import { coursesStats } from './coursesStats';
import { humanizeTypVyucby, plural } from './humanizeAISData';
import { FormItem, PageLayout, PageTitle } from './layout';
import { Link, navigate } from './router';
import { sortAs, sortTable } from './sorting';


export const ZapisZPlanuColumns = [
  ['Moje?', 'moje', null, true],
  [<abbr title="Typ výučby">Typ</abbr>, 'typ_vyucby'],
  [
    'Blok',
    null,
    (predmet) => (
      parseInt(predmet.blok_index || 0, 10) * 1000
        + parseInt(predmet.v_bloku_index || 0, 10)
    ),
  ],
  ['Názov predmetu', 'nazov'],
  ['Skratka predmetu', 'skratka'],
  [<abbr title="Semester">Sem.</abbr>, 'semester', null, true],
  ['Rozsah výučby', 'rozsah_vyucby'],
  ['Kredit', 'kredit', sortAs.number],
  ['Prihlásení', 'pocet_prihlasenych', sortAs.number],
  [<abbr title="Odporúčaný ročník">Odp. ročník</abbr>, 'odporucany_rocnik'],
  ['Jazyk', 'jazyk'],
];
ZapisZPlanuColumns.defaultOrder = 'a1a2a9a3';


export const ZapisZPonukyColumns = [
  ['Moje?', 'moje', null, true],
  [<abbr title="Typ výučby">Typ</abbr>, 'typ_vyucby'],
  ['Blok', 'blok_skratka'],
  ['Názov predmetu', 'nazov'],
  ['Skratka predmetu', 'skratka'],
  [<abbr title="Semester">Sem.</abbr>, 'semester', null, true],
  ['Rozsah výučby', 'rozsah_vyucby'],
  ['Kredit', 'kredit', sortAs.number],
  ['Prihlásení', 'pocet_prihlasenych', sortAs.number],
  ['Jazyk', 'jazyk'],
];
ZapisZPonukyColumns.defaultOrder = 'a3';

export const ZapisVlastnostiColumns = [
  ['Skratka', 'skratka'],
  ['Názov', 'nazov'],
  ['Minimálny kredit', 'minimalny_kredit'],
  ['Poznámka', 'poznamka'],
];

export class ZapisMenu extends Component {

  renderLink = (content, href, active) => {
    return (
      <Link
        className={'btn btn-default' + (active ? ' active' : '')}
        href={href}
      >
        {content}
      </Link>
    );
  }

  render() {
    const { action, cast, zapisnyListKey } = this.props.query;
    return (
      <div>
        <div className="header">
          <PageTitle>Zápis predmetov</PageTitle>
          <div className="pull-right">
            <div className="btn-group">
              {this.renderLink('Môj študijný plán',
                { action: 'zapisZPlanu', cast: 'SC', zapisnyListKey },
                action === 'zapisZPlanu' && cast !== 'SS')}
              {this.renderLink('Predmety štátnej skúšky',
                { action: 'zapisZPlanu', cast: 'SS', zapisnyListKey },
                action === 'zapisZPlanu' && cast === 'SS')}
              {this.renderLink('Hľadať ďalšie predmety',
                { action: 'zapisZPonuky', zapisnyListKey },
                action === 'zapisZPonuky')}
            </div>
          </div>
        </div>
        <div>{this.props.children}</div>
      </div>
    );
  }
}

ZapisMenu.propTypes = {
  query: PropTypes.object.isRequired,
};

export class ZapisTableFooter extends Component {

  constructor(props) {
    super(props);
    this.state = this.parseBloky(props);
  }

  parseBloky = (props) => {
    const bloky = {}, nazvy = {}, semestre = {};
    bloky[''] = [];

    Object
      .keys(props.predmety)
      .forEach((predmetKey) => {
        const predmet = props.predmety[predmetKey];
        semestre[predmet.semestre] = true;
        nazvy[predmet.blok_skratka] = predmet.blok_nazov;
      });

    Object
      .keys(nazvy)
      .sort()
      .forEach((skratka) => {bloky[skratka] = [];});

    Object
      .keys(props.predmety)
      .forEach((predmetKey) => {
        const predmet = props.predmety[predmetKey];
        if (!props.moje[predmet.predmet_key]) {
          return;
        }
        if (predmet.blok_skratka) {
          bloky[predmet.blok_skratka].push(predmet);
        };
        bloky[''].push(predmet);
      });

    const jedinySemester = Object.keys(semestre).length <= 1;

    return { bloky, nazvy, semestre, jedinySemester };
  }

  componentWillReceiveProps(nextProps) {
    this.setState(this.parseBloky(nextProps));
  }

  renderBlok = ({ blok, skratka }) => {
    const stats = coursesStats(blok);
    const { nazvy, jedinySemester } = this.state;

    return (
      <tr key={skratka}>
        <td colSpan="2">{skratka ? 'Súčet bloku' : 'Dokopy'}</td>
        <td>
          {nazvy[skratka]
            ? <abbr title={nazvy[skratka]}>{skratka}</abbr>
            : skratka
          }
        </td>
        <td colSpan="4">
          {stats.spolu.count} {plural(stats.spolu.count, 'predmet', 'predmety', 'predmetov')}
          {!jedinySemester && ` (${stats.zima.count} v zime, ${stats.leto.count}) v lete)`}
        </td>
        <td>
          {stats.spolu.creditsCount}
          {!jedinySemester && ` (${stats.zima.creditsCount}+${stats.leto.creditsCount})`}
        </td>
        <td colSpan="3" />
      </tr>
    );
  }

  render() {
    return (
      <tfoot>
        {Object
          .keys(this.state.bloky)
          .map((skratka) => ({ skratka, blok: this.state.bloky[skratka] }))
          .map(this.renderBlok)
        }
      </tfoot>
    );
  }
}

ZapisTableFooter.propTypes = {
  predmety: PropTypes.object.isRequired,
  moje: PropTypes.object.isRequired,
};

export class ZapisTable extends Component {

  componentWillMount() {
    this.setState({
      odoberanePredmety: {},
      pridavanePredmety: {},
    });
  }

  handleChange = (event) => {
    const predmetKey = event.target.name;
    const predmet = this.props.predmety[predmetKey];

    delete this.state.odoberanePredmety[predmetKey];
    delete this.state.pridavanePredmety[predmetKey];
    if (predmet.moje && !event.target.checked) {
      this.state.odoberanePredmety[predmetKey] = true;
    }
    if (!predmet.moje && event.target.checked) {
      this.state.pridavanePredmety[predmetKey] = true;
    }

    this.forceUpdate();
  }

  handleSave = (event) => {
    event.preventDefault();

    if (this.state.saving) {
      return;
    }

    const predmety = this.props.predmety;

    const odoberanePredmety = [], pridavanePredmety = [];

    Object.keys(predmety).forEach((predmetKey) => {
      if (this.state.odoberanePredmety[predmetKey] && predmety[predmetKey].moje) {
        odoberanePredmety.push(predmety[predmetKey]);
      }
      if (this.state.pridavanePredmety[predmetKey] && !predmety[predmetKey].moje) {
        pridavanePredmety.push(predmety[predmetKey]);
      }
    });

    this.setState({ saving: true });

    const koniec = (odobral, pridal) => {
      if (odobral) {
        odoberanePredmety.forEach((predmet) => {
          RequestCache['pocet_prihlasenych_je_stary' + predmet.predmet_key] = true;
        });
        this.setState({ odoberanePredmety: {} });
      }

      if (pridal) {
        pridavanePredmety.forEach((predmet) => {
          RequestCache['pocet_prihlasenych_je_stary' + predmet.predmet_key] = true;
        });
        this.setState({ pridavanePredmety: {} });
      }

      // Aj ked skoncime neuspechom, je mozne, ze niektore predmety sa zapisali.
      RequestCache.invalidate('get_hodnotenia');
      RequestCache.invalidate('get_predmety');
      RequestCache.invalidate('get_prehlad_kreditov');
      RequestCache.invalidate('get_studenti_zapisani_na_predmet');
      RequestCache.invalidate('zapis_get_zapisane_predmety');
    };

    this.props.odoberPredmety(odoberanePredmety, (message) => {
      if (message) {
        this.setState({ saving: false });
        alert(message);
        koniec(false, false);
      } else {
        this.props.pridajPredmety(pridavanePredmety, (message) => {
          this.setState({ saving: false });
          if (message) {
            alert(message);
            koniec(true, false);
          } else {
            koniec(true, true);
          }
        });
      }
    });
  }

  render() {
    // Chceme, aby sa pre ZapisTable zachoval this.state aj vtedy, ked tabulku
    // nevidno, lebo sme prave zapisali predmety a obnovujeme zoznam predmetov.
    // Takze komponent ZapisTable sa bude renderovat vzdy, aby nikdy nezanikol
    // a neprisiel o state. Niekedy proste nedostane this.props.predmety.
    if (!this.props.predmety || !this.props.akademickyRok) {
      return <span />;
    }

    const { columns, query, message } = this.props;
    let { predmety } = this.props;

    const classes = {}, checked = {};

    Object.keys(predmety).forEach((predmetKey) => {
      checked[predmetKey] = predmety[predmetKey].moje;
      if (this.state.odoberanePredmety[predmetKey] && predmety[predmetKey].moje) {
        classes[predmetKey] = 'danger';
        checked[predmetKey] = false;
      }
      if (this.state.pridavanePredmety[predmetKey] && !predmety[predmetKey].moje) {
        classes[predmetKey] = 'success';
        checked[predmetKey] = true;
      }
    });

    const saveButton = (
      <div className="section">
        <button
          type="submit"
          className="btn btn-primary"
          disabled={Object.keys(classes).length === 0}
        >
          {this.state.saving ? <Loading /> : 'Uložiť zmeny'}
        </button>
      </div>
    );

    let header;
    [predmety, header] = sortTable(
      Object.keys(predmety).map((key) => predmety[key]),
      columns,
      query,
      'predmetySort'
    );

    return (
      <form onSubmit={this.handleSave}>
        {saveButton}
        <table className="table table-condensed table-bordered table-striped table-hover with-buttons-table">
          <thead>{header}</thead>
          <tbody>
            {predmety.map((predmet) => {
              const predmetKey = predmet.predmet_key;
              const href = {
                ...this.props.query,
                modal: 'detailPredmetu',
                modalPredmetKey: predmet.predmet_key,
                modalAkademickyRok: this.props.akademickyRok,
              };
              let nazov = <Link href={href}>{predmet.nazov}</Link>;
              if (predmet.moje) {
                nazov = <strong>{nazov}</strong>;
              }
              if (predmet.aktualnost) {
                nazov = <span><del>{nazov}</del> (nekoná sa)</span>;
              }
              let blok = predmet.blok_skratka;
              if (predmet.blok_nazov) {
                blok = <abbr title={predmet.blok_nazov}>{blok}</abbr>;
              }

              return (
                <tr key={predmetKey} className={classes[predmetKey]}>
                  <td className="text-center">
                    <input
                      type="checkbox"
                      name={predmetKey}
                      checked={checked[predmetKey]}
                      onChange={this.handleChange}
                    />
                  </td>
                  <td>
                    <abbr title={humanizeTypVyucby(predmet.typ_vyucby)}>
                      {predmet.typ_vyucby}
                    </abbr>
                  </td>
                  <td>{blok}</td>
                  <td>{nazov}</td>
                  <td>{predmet.skratka}</td>
                  <td>{predmet.semester}</td>
                  <td>{predmet.rozsah_vyucby}</td>
                  <td>{predmet.kredit}</td>
                  <td>
                    {RequestCache['pocet_prihlasenych_je_stary' + predmetKey]
                      ? (<del>{predmet.pocet_prihlasenych}</del>)
                      : predmet.pocet_prihlasenych
                    }
                    {predmet.maximalne_prihlasenych && '/' + predmet.maximalne_prihlasenych}
                  </td>
                  {columns === ZapisZPlanuColumns && <td>{predmet.odporucany_rocnik}</td>}
                  <td>{predmet.jazyk.replace(/ ,/g, ', ')}</td>
                </tr>
              );
            })}
          </tbody>
          {this.props.showFooter && <ZapisTableFooter predmety={this.props.predmety} moje={checked} />}
          {message && <tfoot><tr><td colSpan={columns.length}>{message}</td></tr></tfoot>}
        </table>
        {saveButton}
      </form>
    );
  }
}

ZapisTable.propTypes = {
  query: PropTypes.object.isRequired,
  predmety: PropTypes.object,
  akademickyRok: PropTypes.string,
  message: PropTypes.node,
  columns: PropTypes.array.isRequired,
  showFooter: PropTypes.bool,
  odoberPredmety: PropTypes.func.isRequired,
  pridajPredmety: PropTypes.func.isRequired,
};

export class ZapisVlastnostiTable extends Component {

  render() {
    const cache = new CacheRequester();
    const { zapisnyListKey } = this.props.query;

    let [vlastnosti, message] = cache.get('zapis_get_vlastnosti_programu', zapisnyListKey) || [];

    if (!vlastnosti) {
      return <Loading requests={cache.missing} />;
    }

    if (!message && !vlastnosti.length) {
      message = 'Študijný plán nemá žiadne poznámky.';
    }

    let header;
    [vlastnosti, header] = sortTable(
      vlastnosti, ZapisVlastnostiColumns, this.props.query, 'vlastnostiSort');

    return (
      <table className="table table-condensed table-bordered table-striped table-hover">
        <thead>{header}</thead>
        <tbody>
          {vlastnosti.map((vlastnost, index) => (
            <tr key={index}>
              <td>{vlastnost.skratka}</td>
              <td>{vlastnost.nazov}</td>
              <td>{vlastnost.minimalny_kredit}</td>
              <td>{vlastnost.poznamka}</td>
            </tr>
          ))}
        </tbody>
        {message && <tfoot><tr><td colSpan={ZapisVlastnostiColumns.length}>{message}</td></tr></tfoot>}
      </table>
    );
  }
}

ZapisVlastnostiTable.propTypes = {
  query: PropTypes.object.isRequired,
};

export class ZapisZPlanuPageContent extends Component {
  getQuery = () => {
    let { zapisnyListKey, cast } = this.props.query;
    cast = (cast === 'SS' ? 'SS' : 'SC');
    return { zapisnyListKey, cast };
  }

  render() {
    const cache = new CacheRequester();
    const { zapisnyListKey, cast } = this.getQuery();

    const [zapisanePredmety, zapisaneMessage] = cache.get(
      'zapis_get_zapisane_predmety', zapisnyListKey, cast
    ) || [];
    const [ponukanePredmety, ponukaneMessage] = cache.get(
      'zapis_plan_vyhladaj', zapisnyListKey, cast
    ) || [];
    const akademickyRok = cache.get('zapisny_list_key_to_akademicky_rok', zapisnyListKey);

    let outerMessage, tableMessage, predmety = {};

    if (zapisaneMessage || ponukaneMessage) {
      outerMessage = <p>{zapisaneMessage || ponukaneMessage}</p>;
    } else if (!cache.loadedAll) {
      outerMessage = <Loading requests={cache.missing} />;
    } else {
      let vidnoZimne = false;

      ponukanePredmety.forEach((predmet) => {
        predmety[predmet.predmet_key] = { moje: false, ...predmet };
        if (predmet.semester === 'Z') {
          vidnoZimne = true;
        }
      });
      zapisanePredmety.forEach((predmet) => {
        const predmetKey = predmet.predmet_key;
        if (!predmety[predmetKey]) {
          if (predmet.semester === 'Z' && !vidnoZimne) {
            return;
          }
          predmety[predmetKey] = { moje: true, ...predmet };
        } else {
          for (let property in predmet) {
            if (predmet[property] !== null && predmet[property] !== undefined) {
              predmety[predmetKey][property] = predmet[property];
            }
          }
          predmety[predmetKey].moje = true;
        }
      });

      if (Object.keys(predmety).length === 0) {
        tableMessage = 'Zoznam ponúkaných predmetov je prázdny.';
      }
    }

    return (
      <ZapisMenu query={this.props.query}>
        {outerMessage}
        <ZapisTable
          query={this.props.query}
          predmety={predmety}
          message={tableMessage}
          akademickyRok={akademickyRok}
          odoberPredmety={this.odoberPredmety}
          pridajPredmety={this.pridajPredmety}
          columns={ZapisZPlanuColumns}
          showFooter
        />
        <h2>Poznámky k študijnému plánu</h2>
        <ZapisVlastnostiTable query={this.props.query} />
      </ZapisMenu>
    );
  }

  pridajPredmety = (predmety, callback) => {
    if (!predmety.length) {
      return callback(null);
    }

    const { zapisnyListKey, cast } = this.getQuery();
    const dvojice = predmety.map((predmet) => [predmet.typ_vyucby, predmet.skratka]);
    sendRpc('zapis_plan_pridaj_predmety', [zapisnyListKey, cast, dvojice], callback);
  }

  odoberPredmety = (predmety, callback) => {
    if (!predmety.length) {
      return callback(null);
    }

    const { zapisnyListKey, cast } = this.getQuery();
    const kluce = predmety.map((predmet) => predmet.predmet_key);
    sendRpc('zapis_odstran_predmety', [zapisnyListKey, cast, kluce], callback);
  }
}

export class ZapisZPlanuPage extends Component {

  render() {
    return (
      <PageLayout query={this.props.query}>
        <ZapisnyListSelector
          query={this.props.query}
          component={ZapisZPlanuPageContent}
        />
      </PageLayout>
    );
  }
}

ZapisZPlanuPage.propTypes = {
  query: PropTypes.object.isRequired,
};

export class ZapisZPonukyForm extends Component {
  componentWillMount() {
    const query = this.props.query;

    this.setState({
      fakulta: query.fakulta,
      stredisko: query.stredisko,
      skratkaPredmetu: query.skratkaPredmetu,
      nazovPredmetu: query.nazovPredmetu,
    });
  }

  handleFieldChange = (event) => {
    this.setState({ [event.target.name]: event.target.value });
  }

  handleSubmit = (event) => {
    event.preventDefault();
    const { zapisnyListKey } = this.props.query;
    navigate({ action: 'zapisZPonuky', zapisnyListKey, ...this.state });
  }

  renderTextInput = (label, name, focus) => {
    return (
      <FormItem label={label}>
        <input
          className="form-item-control"
          name={name}
          autoFocus={focus}
          value={this.state[name]}
          type="text"
          onChange={this.handleFieldChange}
        />
      </FormItem>
    );
  }

  renderSelect = (label, name, items, cache) => {
    return (
      <FormItem label={label}>
        {items ?
          <select
            className="form-item-control"
            name={name}
            value={this.state[name]}
            onChange={this.handleFieldChange}
          >
            {items.map((item) =>
              <option key={item.id} value={item.id}>{item.title}</option>
            )}
          </select> : <Loading requests={cache.missing} />}
      </FormItem>
    );
  }

  render() {
    const cache = new CacheRequester();
    const [fakulty, message] = cache.get('zapis_ponuka_options', this.props.query.zapisnyListKey) || [];

    if (!fakulty) {
      return <Loading requests={cache.missing} />;
    }

    if (message) {
      return <p>{message}</p>;
    }

    return (
      <form onSubmit={this.handleSubmit}>
        {this.renderTextInput('Názov predmetu: ', 'nazovPredmetu', true)}
        {this.renderTextInput('Skratka predmetu: ', 'skratkaPredmetu', false)}
        {this.renderSelect('Fakulta: ', 'fakulta', fakulty, cache)}
        {this.renderTextInput('Stredisko: ', 'stredisko', false)}
        <FormItem>
          <button className="btn btn-primary" type="submit">Vyhľadaj</button>
        </FormItem>
      </form>
    );
  }
}

export class ZapisZPonukyPageContent extends Component {

  render() {
    const cache = new CacheRequester();
    const query = this.props.query;

    let outerMessage, tableMessage, predmety, akademickyRok;

    if (query.fakulta ||
        query.stredisko ||
        query.skratkaPredmetu ||
        query.nazovPredmetu) {
      const [zapisanePredmety, zapisaneMessage] = cache.get(
        'zapis_get_zapisane_predmety', query.zapisnyListKey, 'SC'
      ) || [];
      const [ponukanePredmety, ponukaneMessage] = cache.get('zapis_ponuka_vyhladaj', query.zapisnyListKey,
        query.fakulta || null,
        query.stredisko || null,
        query.skratkaPredmetu || null,
        query.nazovPredmetu || null) || [];
      akademickyRok = cache.get('zapisny_list_key_to_akademicky_rok', query.zapisnyListKey);

      if (zapisaneMessage) {
        outerMessage = <p>{zapisaneMessage}</p>;
      } else if (!cache.loadedAll) {
        outerMessage = <Loading requests={cache.missing} />;
      } else {
        predmety = {};
        ponukanePredmety.forEach((predmet) => {
          predmety[predmet.predmet_key] = { moje: false, ...predmet };
        });
        zapisanePredmety.forEach((predmet) => {
          if (predmety[predmet.predmet_key]) {
            predmety[predmet.predmet_key].moje = true;
          }
        });

        tableMessage = ponukaneMessage;
        if (Object.keys(predmety) === 0 && !tableMessage) {
          tableMessage = 'Podmienkam nevyhovuje žiadny záznam.';
        }
      }
    }

    return (
      <ZapisMenu query={this.props.query}>
        <ZapisZPonukyForm query={this.props.query} />
        {outerMessage}
        {predmety && <h2>Výsledky</h2>}
        <ZapisTable
          query={this.props.query} predmety={predmety} message={tableMessage}
          akademickyRok={akademickyRok}
          odoberPredmety={this.odoberPredmety}
          pridajPredmety={this.pridajPredmety}
          columns={ZapisZPonukyColumns}
        />
      </ZapisMenu>
    );
  }

  pridajPredmety = (predmety, callback) => {
    if (!predmety.length) {
      return callback(null);
    }

    const query = this.props.query;
    const skratky = predmety.map((predmet) => predmet.skratka);
    sendRpc('zapis_ponuka_pridaj_predmety', [query.zapisnyListKey,
      query.fakulta || null,
      query.stredisko || null,
      query.skratkaPredmetu || null,
      query.nazovPredmetu || null,
      skratky], callback);
  }

  odoberPredmety(predmety, callback) {
    if (!predmety.length) {
      return callback(null);
    }

    const query = this.props.query;
    const kluce = predmety.map((predmet) => predmet.predmet_key);
    sendRpc('zapis_odstran_predmety', [query.zapisnyListKey, 'SC', kluce], callback);
  }
}

export class ZapisZPonukyPage extends Component {

  render() {
    return (
      <PageLayout query={this.props.query}>
        <ZapisnyListSelector query={this.props.query} component={ZapisZPonukyPageContent} />
      </PageLayout>
    );
  }
}

ZapisZPonukyPage.propTypes = {
  query: PropTypes.object.isRequired,
};
