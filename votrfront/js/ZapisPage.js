(function () {


Votr.ZapisZPlanuColumns = [
  ["Moje?", 'moje', null, true],
  [<abbr title="Typ výučby">Typ</abbr>, 'typ_vyucby'],
  ["Blok", null, (predmet) => parseInt(predmet.blok_index || 0) * 1000 + parseInt(predmet.v_bloku_index || 0)],
  ["Názov predmetu", 'nazov'],
  ["Skratka predmetu", 'skratka'],
  [<abbr title="Semester">Sem.</abbr>, 'semester', null, true],
  ["Rozsah výučby", 'rozsah_vyucby'],
  ["Kredit", 'kredit', Votr.sortAs.number],
  ["Prihlásení", 'pocet_prihlasenych', Votr.sortAs.number],
  [<abbr title="Odporúčaný ročník">Odp. ročník</abbr>, 'odporucany_rocnik'],
  ["Jazyk", 'jazyk'],
  ["Konanie", 'aktualnost']
];
Votr.ZapisZPlanuColumns.defaultOrder = 'a1a2a9a3';


Votr.ZapisZPonukyColumns = [
  ["Moje?", 'moje', null, true],
  [<abbr title="Typ výučby">Typ</abbr>, 'typ_vyucby'],
  ["Blok", 'blok_skratka'],
  ["Názov predmetu", 'nazov'],
  ["Skratka predmetu", 'skratka'],
  [<abbr title="Semester">Sem.</abbr>, 'semester', null, true],
  ["Rozsah výučby", 'rozsah_vyucby'],
  ["Kredit", 'kredit', Votr.sortAs.number],
  ["Prihlásení", 'pocet_prihlasenych', Votr.sortAs.number],
  ["Jazyk", 'jazyk'],
  ["Konanie", 'aktualnost']
];
Votr.ZapisZPonukyColumns.defaultOrder = 'a3';


Votr.ZapisVlastnostiColumns = [
  ["Skratka", 'skratka'],
  ["Názov", 'nazov'],
  ["Minimálny kredit", 'minimalny_kredit'],
  ["Poznámka", 'poznamka']
];


Votr.ZapisMixin = {
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  renderLink: function (content, href, active) {
    return <Votr.Link className={"btn btn-default" + (active ? " active" : "")} href={href}>{content}</Votr.Link>;
  },

  getInitialState: function () {
    return { pridavanePredmety: {}, odoberanePredmety: {} };
  },

  handleChange: function (event) {
    var cache = new Votr.CacheRequester();
    var [predmety, message] = this.getPredmety(cache);

    if (!predmety) return;

    var predmetKey = event.target.name;
    var predmet = predmety[predmetKey];

    var set = predmet.moje ? this.state.odoberanePredmety : this.state.pridavanePredmety;
    var present = predmet.moje ? !event.target.checked : event.target.checked;

    if (present) {
      set[predmetKey] = true;
    } else {
      delete set[predmetKey];
    }
    this.forceUpdate();
  },

  renderCheckbox: function (predmet) {
    var set = predmet.moje ? this.state.odoberanePredmety : this.state.pridavanePredmety;
    var checked = predmet.moje ? !set[predmet.predmet_key] : set[predmet.predmet_key];
    return <input type="checkbox" name={predmet.predmet_key} checked={checked} onChange={this.handleChange} />;
  },

  handleSave: function (event) {
    event.preventDefault();

    if (this.state.saving) return;

    var cache = new Votr.CacheRequester();
    var {zapisnyListKey, cast} = this.getQuery();
    var [predmety, message] = this.getPredmety(cache);

    if (!predmety) return;

    var odoberanePredmety = [];
    for (var predmet_key in this.state.odoberanePredmety) {
      if (predmety[predmet_key]) {
        odoberanePredmety.push(predmety[predmet_key]);
      }
    }

    var pridavanePredmety = [];
    for (var predmet_key in this.state.pridavanePredmety) {
      if (predmety[predmet_key]) {
        pridavanePredmety.push(predmety[predmet_key]);
      }
    }

    this.setState({ saving: true });

    var spravilNieco = false;

    var koniec = () => {
      if (spravilNieco) {
        pridavanePredmety.forEach((predmet) => {
          Votr.RequestCache['pocet_prihlasenych_je_stary' + predmet.predmet_key] = true;
        });
        odoberanePredmety.forEach((predmet) => {
          Votr.RequestCache['pocet_prihlasenych_je_stary' + predmet.predmet_key] = true;
        });

        Votr.RequestCache.invalidate('get_hodnotenia');
        Votr.RequestCache.invalidate('get_predmety');
        Votr.RequestCache.invalidate('get_prehlad_kreditov');
        Votr.RequestCache.invalidate('get_studenti_zapisani_na_predmet');
        Votr.RequestCache.invalidate('zapis_get_zapisane_predmety');
      }

      this.setState({ pridavanePredmety: {}, odoberanePredmety: {} });
    };

    this.odoberPredmety(odoberanePredmety, (message) => {
      if (message) {
        this.setState({ saving: false });
        alert(message);
        koniec();
      } else {
        if (odoberanePredmety.length) spravilNieco = true;
        this.pridajPredmety(pridavanePredmety, (message) => {
          this.setState({ saving: false });
          if (message) {
            alert(message);
            koniec();
          } else {
            if (pridavanePredmety.length) spravilNieco = true;
            koniec();
          }
        });
      }
    });
  },

  renderSaveButton: function () {
    var disabled = _.isEmpty(this.state.pridavanePredmety) && _.isEmpty(this.state.odoberanePredmety);
    var content = this.state.saving ? <Votr.Loading /> : "Uložiť zmeny";
    return <div className="section">
      <button type="submit" className="btn btn-primary" disabled={disabled}>{content}</button>
    </div>;
  },

  renderTable: function (header, columns, predmety, message, ajRocnik) {
    return <table className="table table-condensed table-bordered table-striped table-hover with-buttons-table">
      <thead>{header}</thead>
      <tbody>
        {predmety.map((predmet) =>
          <tr key={predmet.predmet_key} className={
              this.state.pridavanePredmety[predmet.predmet_key] ? 'success' :
              this.state.odoberanePredmety[predmet.predmet_key] ? 'danger' : null}>
            <td className="text-center">{this.renderCheckbox(predmet)}</td>
            <td><abbr title={Votr.humanizeTypVyucby(predmet.typ_vyucby)}>{predmet.typ_vyucby}</abbr></td>
            <td>{predmet.blok_nazov ? <abbr title={predmet.blok_nazov}>{predmet.blok_skratka}</abbr> : predmet.blok_skratka}</td>
            <td>{predmet.nazov}</td>
            <td>{predmet.skratka}</td>
            <td>{predmet.semester}</td>
            <td>{predmet.rozsah_vyucby}</td>
            <td>{predmet.kredit}</td>
            <td>{Votr.RequestCache['pocet_prihlasenych_je_stary' + predmet.predmet_key] ?
                    <del>{predmet.pocet_prihlasenych}</del> : predmet.pocet_prihlasenych}
                {predmet.maximalne_prihlasenych && "/" + predmet.maximalne_prihlasenych}</td>
            {ajRocnik && <td>{predmet.odporucany_rocnik}</td>}
            <td>{predmet.jazyk.replace(/ ,/g, ', ')}</td>
            <td>{predmet.aktualnost == '' ? 'áno' : 'nie'}</td>
          </tr>
        )}
      </tbody>
      {message && <tfoot><tr><td colSpan={columns.length}>{message}</td></tr></tfoot>}
    </table>;
  },

  render: function () {
    var {action, cast, zapisnyListKey} = this.props.query;
    return <div>
      <div className="header">
        <Votr.PageTitle>Zápis predmetov</Votr.PageTitle>
        <div className="pull-right">
          <div className="btn-group">
            {this.renderLink("Môj študijný plán",
              { action: 'zapisZPlanu', cast: 'SC', zapisnyListKey },
              action == 'zapisZPlanu' && cast != 'SS')}
            {this.renderLink("Predmety štátnej skúšky",
              { action: 'zapisZPlanu', cast: 'SS', zapisnyListKey },
              action == 'zapisZPlanu' && cast == 'SS')}
            {this.renderLink("Hľadať ďalšie predmety",
              { action: 'zapisZPonuky', zapisnyListKey },
              action == 'zapisZPonuky')}
          </div>
        </div>
      </div>
      <div>{this.renderContent()}</div>
    </div>;
  }
};


Votr.ZapisZPlanuPageContent = React.createClass({
  mixins: [Votr.ZapisMixin],

  getQuery: function () {
    var {zapisnyListKey, cast} = this.props.query;
    cast = (cast == 'SS' ? 'SS' : 'SC');
    return {zapisnyListKey, cast};
  },

  getPredmety: function (cache) {
    var {zapisnyListKey, cast} = this.getQuery();

    var [zapisanePredmety, message1] = cache.get('zapis_get_zapisane_predmety', zapisnyListKey, cast) || [];
    var [ponukanePredmety, message2] = cache.get('zapis_plan_vyhladaj', zapisnyListKey, cast) || [];

    if (message1 || message2) {
      return [null, <p>{message1 || message2}</p>];
    }

    if (!zapisanePredmety || !ponukanePredmety) {
      return [null, <Votr.Loading requests={cache.missing} />];
    }

    var vidnoZimne = false;

    var predmety = {};
    ponukanePredmety.forEach((predmet) => {
      predmety[predmet.predmet_key] = _.assign({ moje: false }, predmet);
      if (predmet.semester == 'Z') vidnoZimne = true;
    });
    zapisanePredmety.forEach((predmet) => {
      var predmet_key = predmet.predmet_key;
      if (!predmety[predmet_key]) {
        if (predmet.semester == 'Z' && !vidnoZimne) return;
        predmety[predmet_key] = _.assign({ moje: true }, predmet);
      } else {
        for (var property in predmet) {
          if (predmet[property] !== null && predmet[property] !== undefined) {
            predmety[predmet_key][property] = predmet[property];
          }
        }
        predmety[predmet_key].moje = true;
      }
    });

    return [predmety, null];
  },

  renderNotes: function () {
    var cache = new Votr.CacheRequester();
    var {zapisnyListKey} = this.props.query;

    var [vlastnosti, message] = cache.get('zapis_get_vlastnosti_programu', zapisnyListKey) || [];

    if (!vlastnosti) {
      return <Votr.Loading requests={cache.missing} />;
    }

    if (!message && !vlastnosti.length) {
      message = "Študijný plán nemá žiadne poznámky.";
    }

    var [vlastnosti, header] = Votr.sortTable(
      vlastnosti, Votr.ZapisVlastnostiColumns, this.props.query, 'vlastnostiSort');

    return <table className="table table-condensed table-bordered table-striped table-hover">
      <thead>{header}</thead>
      <tbody>
        {vlastnosti.map((vlastnost, index) =>
          <tr key={index}>
            <td>{vlastnost.skratka}</td>
            <td>{vlastnost.nazov}</td>
            <td>{vlastnost.minimalny_kredit}</td>
            <td>{vlastnost.poznamka}</td>
          </tr>
        )}
      </tbody>
      {message && <tfoot><tr><td colSpan={Votr.ZapisVlastnostiColumns.length}>{message}</td></tr></tfoot>}
    </table>;
  },

  renderContent: function () {
    var cache = new Votr.CacheRequester();
    var [predmety, message] = this.getPredmety(cache);

    if (!predmety) return message;

    var [predmety, header] = Votr.sortTable(
      _.values(predmety), Votr.ZapisZPlanuColumns, this.props.query, 'predmetySort');

    if (!message && !predmety.length) {
      message = "Zoznam ponúkaných predmetov je prázdny.";
    }

    return <form onSubmit={this.handleSave}>
      {this.renderSaveButton()}
      {this.renderTable(header, Votr.ZapisZPlanuColumns, predmety, message, true)}
      {this.renderSaveButton()}
      <h2>Poznámky k študijnému plánu</h2>
      {this.renderNotes()}
    </form>;
  },

  pridajPredmety: function (predmety, callback) {
    if (!predmety.length) return callback(null);

    var {zapisnyListKey, cast} = this.getQuery();
    var dvojice = predmety.map((predmet) => [predmet.typ_vyucby, predmet.skratka]);
    Votr.sendRpc('zapis_plan_pridaj_predmety', [zapisnyListKey, cast, dvojice], callback);
  },

  odoberPredmety: function (predmety, callback) {
    if (!predmety.length) return callback(null);

    var {zapisnyListKey, cast} = this.getQuery();
    var kluce = predmety.map((predmet) => predmet.predmet_key);
    Votr.sendRpc('zapis_odstran_predmety', [zapisnyListKey, cast, kluce], callback);
  }
});


Votr.ZapisZPlanuPage = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  render: function () {
    return <Votr.PageLayout query={this.props.query}>
      <Votr.ZapisnyListSelector query={this.props.query} component={Votr.ZapisZPlanuPageContent} />
    </Votr.PageLayout>;
  }
});


Votr.ZapisZPonukyForm = React.createClass({
  getInitialState: function () {
    var query = this.props.query;
    return {
      fakulta: query.fakulta,
      stredisko: query.stredisko,
      skratkaPredmetu: query.skratkaPredmetu,
      nazovPredmetu: query.nazovPredmetu
    };
  },

  handleFieldChange: function (event) {
    this.setState(_.zipObject([[event.target.name, event.target.value]]));
  },

  handleSubmit: function (event) {
    event.preventDefault();
    var {zapisnyListKey} = this.props.query;
    Votr.navigate(_.assign({ action: 'zapisZPonuky', zapisnyListKey }, this.state));
  },

  renderTextInput: function (label, name, focus) {
    return <Votr.FormItem label={label}>
      <input className="form-item-control" name={name} autoFocus={focus}
             value={this.state[name]} type="text" onChange={this.handleFieldChange} />
    </Votr.FormItem>;
  },

  renderSelect: function (label, name, items, cache) {
    return <Votr.FormItem label={label}>
      {items ?
        <select className="form-item-control" name={name} value={this.state[name]} onChange={this.handleFieldChange}>
          {items.map((item) =>
            <option key={item.id} value={item.id}>{item.title}</option>
          )}
        </select> : <Votr.Loading requests={cache.missing} />}
    </Votr.FormItem>;
  },

  render: function () {
    var cache = new Votr.CacheRequester();
    var [fakulty, message] = cache.get('zapis_ponuka_options', this.props.query.zapisnyListKey) || [];

    if (!fakulty) {
      return <Votr.Loading requests={cache.missing} />;
    }

    if (message) {
      return <p>{message}</p>;
    }

    return <form onSubmit={this.handleSubmit}>
      {this.renderTextInput("Názov predmetu: ", "nazovPredmetu", true)}
      {this.renderTextInput("Skratka predmetu: ", "skratkaPredmetu", false)}
      {this.renderSelect("Fakulta: ", "fakulta", fakulty, cache)}
      {this.renderTextInput("Stredisko: ", "stredisko", false)}
      <Votr.FormItem>
        <button className="btn btn-primary" type="submit">Vyhľadaj</button>
      </Votr.FormItem>
    </form>;
  }
});


Votr.ZapisZPonukyPageContent = React.createClass({
  mixins: [Votr.ZapisMixin],

  getQuery: function () {
    var {zapisnyListKey} = this.props.query;
    return { zapisnyListKey, cast: 'SC' };
  },

  getPredmety: function (cache) {
    var query = this.props.query;
    var {zapisnyListKey, cast} = this.getQuery();

    if (!query.fakulta &&
        !query.stredisko &&
        !query.skratkaPredmetu &&
        !query.nazovPredmetu) {
      return [null, null];
    }

    var [zapisanePredmety, message1] = cache.get('zapis_get_zapisane_predmety', zapisnyListKey, cast) || [];
    var [ponukanePredmety, message2] = cache.get('zapis_ponuka_vyhladaj', zapisnyListKey,
        query.fakulta || null,
        query.stredisko || null,
        query.skratkaPredmetu || null,
        query.nazovPredmetu || null) || [];

    if (message1) {
      return [null, <p>{message1}</p>];
    }

    if (!zapisanePredmety || !ponukanePredmety) {
      return [null, <Votr.Loading requests={cache.missing} />];
    }

    var predmety = {};
    ponukanePredmety.forEach((predmet) => {
      predmety[predmet.predmet_key] = _.assign({ moje: false }, predmet);
    });
    zapisanePredmety.forEach((predmet) => {
      if (predmety[predmet.predmet_key]) {
        predmety[predmet.predmet_key].moje = true;
      }
    });

    return [predmety, message2];
  },

  renderResults: function () {
    var cache = new Votr.CacheRequester();
    var [predmety, message] = this.getPredmety(cache);

    if (!predmety) return message;

    var [predmety, header] = Votr.sortTable(
      _.values(predmety), Votr.ZapisZPonukyColumns, this.props.query, 'predmetySort');

    if (!message && !predmety.length) {
      message = "Podmienkam nevyhovuje žiadny záznam.";
    }

    return <form onSubmit={this.handleSave}>
      <h2>Výsledky</h2>
      {this.renderSaveButton()}
      {this.renderTable(header, Votr.ZapisZPonukyColumns, predmety, message, false)}
      {this.renderSaveButton()}
    </form>;
  },

  renderContent: function () {
    return <div>
      <Votr.ZapisZPonukyForm query={this.props.query} />
      {this.renderResults()}
    </div>;
  },

  pridajPredmety: function (predmety, callback) {
    if (!predmety.length) return callback(null);

    var query = this.props.query;
    var {zapisnyListKey, cast} = this.getQuery();
    var skratky = predmety.map((predmet) => predmet.skratka);
    Votr.sendRpc('zapis_ponuka_pridaj_predmety', [zapisnyListKey,
        query.fakulta || null,
        query.stredisko || null,
        query.skratkaPredmetu || null,
        query.nazovPredmetu || null,
        skratky], callback);
  },

  odoberPredmety: function (predmety, callback) {
    if (!predmety.length) return callback(null);

    var {zapisnyListKey, cast} = this.getQuery();
    var kluce = predmety.map((predmet) => predmet.predmet_key);
    Votr.sendRpc('zapis_odstran_predmety', [zapisnyListKey, cast, kluce], callback);
  }
});


Votr.ZapisZPonukyPage = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  render: function () {
    return <Votr.PageLayout query={this.props.query}>
      <Votr.ZapisnyListSelector query={this.props.query} component={Votr.ZapisZPonukyPageContent} />
    </Votr.PageLayout>;
  }
});


})();
