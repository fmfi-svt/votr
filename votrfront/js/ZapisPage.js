
import PropTypes from 'prop-types';
import React from 'react';
import _ from 'lodash';
import { ZapisnyListSelector } from './ZapisnyListSelector';
import { CacheRequester, Loading, RequestCache, sendRpc } from './ajax';
import { coursesStats } from './coursesStats';
import { humanizeTypVyucby, plural } from './humanizeAISData';
import { FormItem, PageLayout, PageTitle } from './layout';
import { Link, navigate, queryConsumer } from './router';
import { sortAs, SortableTable } from './sorting';


const typVyucbyColumn = {
  label: <abbr title="Typ výučby">Typ</abbr>,
  prop: "typ_vyucby",
  cell: predmet => (
    <abbr title={humanizeTypVyucby(predmet.typ_vyucby)}>
      {predmet.typ_vyucby}
    </abbr>
  )
};
const skratkaColumn = {
  label: "Skratka predmetu",
  prop: "skratka",
  hiddenClass: ["hidden-xs", "hidden-sm"]
};
const semesterColumn = {
  label: "Semester",
  shortLabel: <abbr title="Semester">Sem.</abbr>,
  prop: "semester",
  preferDesc: true
};
const rozsahVyucbyColumn = {
  label: "Rozsah výučby",
  prop: "rozsah_vyucby",
  hiddenClass: ["hidden-xs", "hidden-sm"]
};
const kreditColumn = {
  label: "Kredit",
  prop: "kredit",
  process: sortAs.number,
  hiddenClass: ["hidden-xs"]
};
const prihlaseniColumn = {
  label: "Prihlásení",
  prop: "pocet_prihlasenych",
  process: sortAs.number,
  cell: predmet =>
    <React.Fragment>
      {RequestCache["pocet_prihlasenych_je_stary" + predmet.predmet_key] ? (
        <del>{predmet.pocet_prihlasenych}</del>
      ) : (
        predmet.pocet_prihlasenych
      )}
      {predmet.maximalne_prihlasenych && "/" + predmet.maximalne_prihlasenych}
    </React.Fragment>,
  hiddenClass: ["hidden-xs"]
};
const jazykColumn = {
  label: "Jazyk",
  prop: "jazyk",
  cell: predmet => predmet.jazyk.replace(/ ,/g, ", "),
  hiddenClass: ["hidden-xs", "hidden-sm"]
};


export var ZapisZPlanuColumns = [
  typVyucbyColumn,
  {
    label: "Blok",
    process: (predmet) => parseInt(predmet.blok_index || 0) * 1000 + parseInt(predmet.v_bloku_index || 0),
    hiddenClass: ["hidden-xs", "hidden-sm"],
    cell:  predmet =>
      predmet.blok_nazov ? (
        <abbr title={predmet.blok_nazov}>{predmet.blok_skratka}</abbr>
      ) : (
        predmet.blok_skratka
      )
  },
  skratkaColumn,
  semesterColumn,
  rozsahVyucbyColumn,
  kreditColumn,
  prihlaseniColumn,
  {
    label: <abbr title="Odporúčaný ročník">Odp. ročník</abbr>,
    prop: 'odporucany_rocnik',
    hiddenClass: ["hidden-xs", "hidden-sm"]
  },
  jazykColumn
];
ZapisZPlanuColumns.defaultOrder = 'a1a2a9a3';


export var ZapisZPonukyColumns = [
  typVyucbyColumn,
  { label: "Blok", prop: 'blok_skratka', hiddenClass: ["hidden-xs", "hidden-sm"] },
  skratkaColumn,
  semesterColumn,
  rozsahVyucbyColumn,
  kreditColumn,
  prihlaseniColumn,
  jazykColumn
];
ZapisZPonukyColumns.defaultOrder = 'a3';


export var ZapisVlastnostiColumns = [
  {label: "Skratka", prop: 'skratka', expansionMark: true},
  {label: "Názov", prop: 'nazov'},
  {label: "Minimálny kredit", prop: 'minimalny_kredit'},
  {label: "Poznámka", prop: 'poznamka'}
];


function ZapisLink(props) {
  return <Link className={"btn btn-default" + (props.active ? " active" : "")} href={props.href}>{props.label}</Link>;
}


export function ZapisMenu(props) {
  var {action, cast, zapisnyListKey} = props.query;
  return (
    <div className="header">
      <PageTitle>Zápis predmetov</PageTitle>
      <div className="pull-right">
        <div className="btn-group">
          <ZapisLink
            label="Môj študijný plán"
            href={{ action: 'zapisZPlanu', cast: 'SC', zapisnyListKey }}
            active={action == 'zapisZPlanu' && cast != 'SS'}
          />
          <ZapisLink
            label="Predmety štátnej skúšky"
            href={{ action: 'zapisZPlanu', cast: 'SS', zapisnyListKey }}
            active={action == 'zapisZPlanu' && cast == 'SS'}
          />
          <ZapisLink
            label="Hľadať ďalšie predmety"
            href={{ action: 'zapisZPonuky', zapisnyListKey }}
            active={action == 'zapisZPonuky'}
          />
        </div>
      </div>
    </div>
  );
}

ZapisMenu.propTypes = {
  query: PropTypes.object.isRequired
};


export function ZapisTableFooter(props) {
  var bloky = {}, nazvy = {}, semestre = {};
  _.forEach(props.predmety, (predmet) => {
    semestre[predmet.semestre] = true;
    nazvy[predmet.blok_skratka] = predmet.blok_nazov;
  });

  _.forEach(_.sortBy(_.keys(nazvy)), (skratka) => bloky[skratka] = []);
  bloky[''] = [];

  _.forEach(props.predmety, (predmet) => {
    if (!props.moje[predmet.predmet_key]) return;
    if (predmet.blok_skratka) bloky[predmet.blok_skratka].push(predmet);
    bloky[''].push(predmet);
  });

  var jedinySemester = _.keys(semestre).length <= 1;

  return (
    <React.Fragment>
      {_.map(bloky, (blok, skratka) => {
        var stats = coursesStats(blok);
        return (
          <React.Fragment key={skratka}>
            <tr key={skratka} className={props.fullTable ? null : "hidden-xs hidden-sm"}>
              <td colSpan="2">{skratka ? "Súčet bloku" : "Dokopy"}</td>
              <td>{nazvy[skratka] ? <abbr title={nazvy[skratka]}>{skratka}</abbr> : skratka}</td>
              <td colSpan="4">
                {stats.spolu.count} {plural(stats.spolu.count, "predmet", "predmety", "predmetov")}
                {!jedinySemester && " ("+stats.zima.count+" v zime, "+stats.leto.count+" v lete)"}
              </td>
              <td>
                {stats.spolu.creditsEnrolled}
                {!jedinySemester && " ("+stats.zima.creditsEnrolled+"+"+stats.leto.creditsEnrolled+")"}
              </td>
              <td colSpan="3"></td>
            </tr>
            <tr key={skratka+"sm"} className={"hidden-md hidden-lg"}>
              <td>{skratka ? "Súčet bloku" : "Dokopy"}</td>
              <td>{nazvy[skratka] ? <abbr title={nazvy[skratka]}>{skratka}</abbr> : skratka}</td>
              <td colSpan="2">
                {stats.spolu.count} {plural(stats.spolu.count, "predmet", "predmety", "predmetov")}
                {!jedinySemester && " ("+stats.zima.count+" v zime, "+stats.leto.count+" v lete)"}
                <span className="hidden-sm">
                  {", "}
                  {stats.spolu.creditsEnrolled}
                  {!jedinySemester && " ("+stats.zima.creditsEnrolled+"+"+stats.leto.creditsEnrolled+")"}
                  {" " + plural(stats.spolu.creditsEnrolled, "kredit", "kredity", "kreditov")}
                </span>
              </td>
              <td colSpan="2" className="hidden-xs">
                {stats.spolu.creditsEnrolled}
                {!jedinySemester && " ("+stats.zima.creditsEnrolled+"+"+stats.leto.creditsEnrolled+")"}
              </td>
            </tr>
          </React.Fragment>
        );
      })}
    </React.Fragment>
  );
}

ZapisTableFooter.propTypes = {
  predmety: PropTypes.object.isRequired,
  moje: PropTypes.object.isRequired
};


export class ZapisTable extends React.Component {
  static propTypes = {
    query: PropTypes.object.isRequired,
    predmety: PropTypes.object,
    akademickyRok: PropTypes.string,
    message: PropTypes.node,
    columns: PropTypes.array.isRequired,
    showFooter: PropTypes.bool,
    odoberPredmety: PropTypes.func.isRequired,
    pridajPredmety: PropTypes.func.isRequired
  };

  state = { odoberanePredmety: {}, pridavanePredmety: {} };

  handleChange = (event) => {
    var predmetKey = event.target.name;
    var predmet = this.props.predmety[predmetKey];

    delete this.state.odoberanePredmety[predmetKey];
    delete this.state.pridavanePredmety[predmetKey];
    if (predmet.moje && !event.target.checked) this.state.odoberanePredmety[predmetKey] = true;
    if (!predmet.moje && event.target.checked) this.state.pridavanePredmety[predmetKey] = true;

    this.forceUpdate();
  }

  handleSave = (event) => {
    event.preventDefault();

    if (this.state.saving) return;

    var predmety = this.props.predmety;

    var odoberanePredmety = [], pridavanePredmety = [];
    for (var predmet_key in predmety) {
      if (this.state.odoberanePredmety[predmet_key] && predmety[predmet_key].moje) {
        odoberanePredmety.push(predmety[predmet_key]);
      }
      if (this.state.pridavanePredmety[predmet_key] && !predmety[predmet_key].moje) {
        pridavanePredmety.push(predmety[predmet_key]);
      }
    }

    this.setState({ saving: true });

    var koniec = (odobral, pridal) => {
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

    var {predmety, columns, query, message} = this.props;

    var classes = {}, checked = {};
    for (var predmet_key in predmety) {
      checked[predmet_key] = predmety[predmet_key].moje;
      if (this.state.odoberanePredmety[predmet_key] && predmety[predmet_key].moje) {
        classes[predmet_key] = 'danger';
        checked[predmet_key] = false;
      }
      if (this.state.pridavanePredmety[predmet_key] && !predmety[predmet_key].moje) {
        classes[predmet_key] = 'success';
        checked[predmet_key] = true;
      }
    }

    var saveButton = <div className="section">
      <button type="submit" className="btn btn-primary" disabled={_.isEmpty(classes)}>
        {this.state.saving ? <Loading /> : "Uložiť zmeny"}
      </button>
    </div>;

    // mojeColumn
    const mojeColumn = {
      label: "Moje?",
      prop: "moje",
      preferDesc: true,
      colProps: () => ({ className: "text-center" }),
      cell: (predmet, query) => (
        <input
          type="checkbox"
          name={predmet.predmet_key}
          checked={checked[predmet.predmet_key]}
          onChange={this.handleChange}
        />
      )
    };

    // nazovColumn
    const nazovColumn = {
      label: "Názov predmetu",
      prop: "nazov",
      expansionMark: true,
      cell: predmet => {
        var href = {
          ...this.props.query,
          modal: "detailPredmetu",
          modalPredmetKey: predmet.predmet_key,
          modalAkademickyRok: this.props.akademickyRok
        };
        var nazov = <Link href={href}>{predmet.nazov}</Link>;
        if (predmet.moje) nazov = <strong>{nazov}</strong>;
        if (predmet.aktualnost)
        nazov = (
          <React.Fragment>
          <del>{nazov}</del> (nekoná sa)
          </React.Fragment>
        );
        return nazov;
      }
    };
    columns = [mojeColumn, ...columns.slice(0, 2), nazovColumn, ...columns.slice(2)];

    const footer = fullTable =>
      this.props.showFooter && (
        <ZapisTableFooter
          predmety={this.props.predmety}
          moje={checked}
          fullTable={fullTable}
        />
      );

    return <form onSubmit={this.handleSave}>
      {saveButton}
      <SortableTable
        items={_.values(predmety)}
        columns={columns}
        queryKey="predmetySort"
        footer={footer}
        message={message}
      />
      {saveButton}
    </form>;
  }
}


export function ZapisVlastnostiTable(props) {
  var cache = new CacheRequester();
  var {zapisnyListKey} = props.query;

  var [vlastnosti, message] = cache.get('zapis_get_vlastnosti_programu', zapisnyListKey) || [];

  if (!vlastnosti) {
    return <Loading requests={cache.missing} />;
  }

  if (!message && !vlastnosti.length) {
    message = "Študijný plán nemá žiadne poznámky.";
  }

  return (
    <SortableTable
      items={vlastnosti}
      columns={ZapisVlastnostiColumns}
      queryKey="vlastnostiSort"
      message={message}
    />
  );
}

ZapisVlastnostiTable.propTypes = {
  query: PropTypes.object.isRequired
};


export class ZapisZPlanuPageContent extends React.Component {
  getQuery() {
    var {zapisnyListKey, cast} = this.props.query;
    cast = (cast == 'SS' ? 'SS' : 'SC');
    return {zapisnyListKey, cast};
  }

  render() {
    var cache = new CacheRequester();
    var {zapisnyListKey, cast} = this.getQuery();

    var [zapisanePredmety, zapisaneMessage] = cache.get('zapis_get_zapisane_predmety', zapisnyListKey, cast) || [];
    var [ponukanePredmety, ponukaneMessage] = cache.get('zapis_plan_vyhladaj', zapisnyListKey, cast) || [];
    var akademickyRok = cache.get('zapisny_list_key_to_akademicky_rok', zapisnyListKey);

    var outerMessage, tableMessage, predmety;

    if (zapisaneMessage || ponukaneMessage) {
      outerMessage = <p>{zapisaneMessage || ponukaneMessage}</p>;
    } else if (!cache.loadedAll) {
      outerMessage = <Loading requests={cache.missing} />;
    } else {
      var vidnoZimne = false;

      predmety = {};
      ponukanePredmety.forEach((predmet) => {
        predmety[predmet.predmet_key] = { moje: false, ...predmet };
        if (predmet.semester == 'Z') vidnoZimne = true;
      });
      zapisanePredmety.forEach((predmet) => {
        var predmet_key = predmet.predmet_key;
        if (!predmety[predmet_key]) {
          if (predmet.semester == 'Z' && !vidnoZimne) return;
          predmety[predmet_key] = { moje: true, ...predmet };
        } else {
          for (var property in predmet) {
            if (predmet[property] !== null && predmet[property] !== undefined) {
              predmety[predmet_key][property] = predmet[property];
            }
          }
          predmety[predmet_key].moje = true;
        }
      });

      if (_.isEmpty(predmety)) {
        tableMessage = "Zoznam ponúkaných predmetov je prázdny.";
      }
    }

    return <React.Fragment>
      <ZapisMenu query={this.props.query} />
      {outerMessage}
      <ZapisTable
          query={this.props.query} predmety={predmety} message={tableMessage}
          akademickyRok={akademickyRok}
          odoberPredmety={this.odoberPredmety}
          pridajPredmety={this.pridajPredmety}
          columns={ZapisZPlanuColumns} showFooter={true} />
      <h2>Poznámky k študijnému plánu</h2>
      <ZapisVlastnostiTable query={this.props.query} />
    </React.Fragment>;
  }

  pridajPredmety = (predmety, callback) => {
    if (!predmety.length) return callback(null);

    var {zapisnyListKey, cast} = this.getQuery();
    var dvojice = predmety.map((predmet) => [predmet.typ_vyucby, predmet.skratka]);
    sendRpc('zapis_plan_pridaj_predmety', [zapisnyListKey, cast, dvojice], callback);
  }

  odoberPredmety = (predmety, callback) => {
    if (!predmety.length) return callback(null);

    var {zapisnyListKey, cast} = this.getQuery();
    var kluce = predmety.map((predmet) => predmet.predmet_key);
    sendRpc('zapis_odstran_predmety', [zapisnyListKey, cast, kluce], callback);
  }
}


export function ZapisZPlanuPage() {
  return (
    <PageLayout>
      <ZapisnyListSelector>
        {queryConsumer(query => <ZapisZPlanuPageContent query={query} />)}
      </ZapisnyListSelector>
    </PageLayout>
  );
}


export class ZapisZPonukyForm extends React.Component {
  constructor(props) {
    super(props);
    var query = props.query;
    this.state = {
      fakulta: query.fakulta,
      stredisko: query.stredisko,
      skratkaPredmetu: query.skratkaPredmetu,
      nazovPredmetu: query.nazovPredmetu
    };
  }

  handleFieldChange = (event) => {
    this.setState({ [event.target.name]: event.target.value });
  }

  handleSubmit = (event) => {
    event.preventDefault();
    var {zapisnyListKey} = this.props.query;
    navigate({ action: 'zapisZPonuky', zapisnyListKey, ...this.state });
  }

  renderTextInput(label, name, focus) {
    return <FormItem label={label}>
      <input className="form-item-control" name={name} autoFocus={focus}
             value={this.state[name]} type="text" onChange={this.handleFieldChange} />
    </FormItem>;
  }

  renderSelect(label, name, items, cache) {
    return <FormItem label={label}>
      {items ?
        <select className="form-item-control" name={name} value={this.state[name]} onChange={this.handleFieldChange}>
          {items.map((item) =>
            <option key={item.id} value={item.id}>{item.title}</option>
          )}
        </select> : <Loading requests={cache.missing} />}
    </FormItem>;
  }

  render() {
    var cache = new CacheRequester();
    var [fakulty, message] = cache.get('zapis_ponuka_options', this.props.query.zapisnyListKey) || [];

    if (!fakulty) {
      return <Loading requests={cache.missing} />;
    }

    if (message) {
      return <p>{message}</p>;
    }

    return <form onSubmit={this.handleSubmit}>
      {this.renderTextInput("Názov predmetu: ", "nazovPredmetu", true)}
      {this.renderTextInput("Skratka predmetu: ", "skratkaPredmetu", false)}
      {this.renderSelect("Fakulta: ", "fakulta", fakulty, cache)}
      {this.renderTextInput("Stredisko: ", "stredisko", false)}
      <FormItem>
        <button className="btn btn-primary" type="submit">Vyhľadaj</button>
      </FormItem>
    </form>;
  }
}


export class ZapisZPonukyPageContent extends React.Component {
  render() {
    var cache = new CacheRequester();
    var query = this.props.query;

    var outerMessage, tableMessage, predmety, akademickyRok;

    if (query.fakulta ||
        query.stredisko ||
        query.skratkaPredmetu ||
        query.nazovPredmetu) {
      var [zapisanePredmety, zapisaneMessage] = cache.get('zapis_get_zapisane_predmety', query.zapisnyListKey, 'SC') || [];
      var [ponukanePredmety, ponukaneMessage] = cache.get('zapis_ponuka_vyhladaj', query.zapisnyListKey,
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
        var predmety = {};
        ponukanePredmety.forEach((predmet) => {
          predmety[predmet.predmet_key] = { moje: false, ...predmet };
        });
        zapisanePredmety.forEach((predmet) => {
          if (predmety[predmet.predmet_key]) {
            predmety[predmet.predmet_key].moje = true;
          }
        });

        tableMessage = ponukaneMessage;
        if (_.isEmpty(predmety) && !tableMessage) {
          tableMessage = "Podmienkam nevyhovuje žiadny záznam.";
        }
      }
    }

    return <React.Fragment>
      <ZapisMenu query={this.props.query} />
      <ZapisZPonukyForm query={this.props.query} />
      {outerMessage}
      {predmety && <h2>Výsledky</h2>}
      <ZapisTable
          query={this.props.query} predmety={predmety} message={tableMessage}
          akademickyRok={akademickyRok}
          odoberPredmety={this.odoberPredmety}
          pridajPredmety={this.pridajPredmety}
          columns={ZapisZPonukyColumns} />
    </React.Fragment>;
  }

  pridajPredmety = (predmety, callback) => {
    if (!predmety.length) return callback(null);

    var query = this.props.query;
    var skratky = predmety.map((predmet) => predmet.skratka);
    sendRpc('zapis_ponuka_pridaj_predmety', [query.zapisnyListKey,
        query.fakulta || null,
        query.stredisko || null,
        query.skratkaPredmetu || null,
        query.nazovPredmetu || null,
        skratky], callback);
  }

  odoberPredmety = (predmety, callback) => {
    if (!predmety.length) return callback(null);

    var query = this.props.query;
    var kluce = predmety.map((predmet) => predmet.predmet_key);
    sendRpc('zapis_odstran_predmety', [query.zapisnyListKey, 'SC', kluce], callback);
  }
}


export function ZapisZPonukyPage() {
  return (
    <PageLayout>
      <ZapisnyListSelector>
        {queryConsumer(query => <ZapisZPonukyPageContent query={query} />)}
      </ZapisnyListSelector>
    </PageLayout>
  );
}
