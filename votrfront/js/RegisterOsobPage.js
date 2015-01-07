(function () {


Votr.RegisterOsobColumns = [
  ["Plné meno", 'plne_meno', Votr.sortAs.personName],
  ["E-mail", 'email']
];
Votr.RegisterOsobColumns.defaultOrder = 'a0';

Votr.RegisterOsobForm = React.createClass({
  getInitialState: function () {
    var query = this.props.query;
    return {
      meno: query.meno,
      priezvisko: query.priezvisko,
      absolventi: query.absolventi,
      studenti: query.studenti,
      zamestnanci: query.zamestnanci,
      akademickyRok: query.akademickyRok || Votr.currentAcademicYear(),
      fakulta: query.fakulta,
      skratkaSp: query.skratkaSp,
      uchadzaciRocnik: query.uchadzaciRocnik,
      prvyRocnik: query.prvyRocnik,
      druhyRocnik: query.druhyRocnik,
      tretiRocnik: query.tretiRocnik,
      stvrtyRocnik: query.stvrtyRocnik,
      piatyRocnik: query.piatyRocnik,
      siestyRocnik: query.siestyRocnik,
      siedmyRocnik: query.siedmyRocnik,
      osmyRocnik: query.osmyRocnik,
      absolventiRocnik: query.absolventiRocnik
    };
  },

  handleFieldChange: function (event) {
    this.setState(_.zipObject([[event.target.name, event.target.value]]));
  },

  handleCheckBoxChange: function (event) {
    this.setState(_.zipObject([[event.target.name, String(event.target.checked)]]));
  },

  handleSubmit: function(event) {
    event.preventDefault();
    Votr.navigate(_.assign({ action: 'registerOsob' }, this.state));
  },

  renderTextInput: function(label, name, focus) {
    return <Votr.FormItem label={label}>
      <input className="form-item-control" name={name} autoFocus={focus}
             value={this.state[name]} type="text" onChange={this.handleFieldChange} />
    </Votr.FormItem>;
  },

  renderSelect: function(label, name, items, cache) {
    return <Votr.FormItem label={label}>
      {items ?
        <select className="form-item-control" name={name} value={this.state[name]} onChange={this.handleFieldChange}>
          {items.map((item) =>
            <option key={item.id} value={item.id}>{item.title}</option>
          )}
        </select> : <Votr.Loading requests={cache.missing} />}
    </Votr.FormItem>;
  },

  renderCheckbox: function(label, name) {
    return <label>
      <input name={name} checked={this.state[name] == "true"} type="checkbox" onChange={this.handleCheckBoxChange} />
      {label}
    </label>;
  },

  render: function () {
    var cache = new Votr.CacheRequester();
    var akademickeRoky = cache.get('get_register_osob_akademicky_rok_options');
    var fakulty = cache.get('get_register_osob_fakulty');

    return <form onSubmit={this.handleSubmit}>
      {this.renderTextInput("Priezvisko: ", "priezvisko", true)}
      {this.renderTextInput("Meno: ", "meno", false)}
      {this.renderSelect("Fakulta: ", "fakulta", fakulty, cache)}
      {this.renderTextInput("Študijný program (skratka): ", "skratkaSp", false)}
      {this.renderSelect("Akademický rok: ", "akademickyRok", akademickeRoky, cache)}
      <div className="form-item">
        <div className="col-sm-4 form-item-label">Typ osoby:</div>
        <div className="col-sm-8">
          {this.renderCheckbox(" Absolventi ", "absolventi")}
          {this.renderCheckbox(" Študenti ", "studenti")}
          {this.renderCheckbox(" Zamestnanci ", "zamestnanci")}
        </div>
      </div>
      <div className="form-item">
        <div className="col-sm-4 form-item-label">Rok štúdia:</div>
        <div className="col-sm-8">
          {this.renderCheckbox(" 1. ", 'prvyRocnik')}
          {this.renderCheckbox(" 2. ", 'druhyRocnik')}
          {this.renderCheckbox(" 3. ", 'tretiRocnik')}
          {this.renderCheckbox(" 4. ", 'stvrtyRocnik')}
          {this.renderCheckbox(" 5. ", 'piatyRocnik')}
          {this.renderCheckbox(" 6. ", 'siestyRocnik')}
          {this.renderCheckbox(" 7. ", 'siedmyRocnik')}
          {this.renderCheckbox(" 8. ", 'osmyRocnik')}
          <br/>
          {this.renderCheckbox(" Uchádzači ", 'uchadzaciRocnik')}
          {this.renderCheckbox(" Absolventi ", 'absolventiRocnik')}
        </div>
      </div>
      <Votr.FormItem>
        <button className="btn btn-primary" type="submit">Vyhľadaj</button>
      </Votr.FormItem>
    </form>;
  },
});

Votr.RegisterOsobResultTable = React.createClass({
  render: function () {
    var cache = new Votr.CacheRequester();
    var query = this.props.query;

    if(!query.akademickyRok ||
       !(query.meno ||
         query.priezvisko ||
         query.absolventi == "true" ||
         query.studenti == "true" ||
         query.zamestnanci == "true" ||
         query.fakulta ||
         query.skratkaSp ||
         query.uchadzaciRocnik == "true" ||
         query.prvyRocnik == "true" ||
         query.druhyRocnik == "true" ||
         query.tretiRocnik == "true" ||
         query.stvrtyRocnik == "true" ||
         query.piatyRocnik == "true" ||
         query.siestyRocnik == "true" ||
         query.siedmyRocnik == "true" ||
         query.osmyRocnik == "true" ||
         query.absolventiRocnik == "true")) {
      return null;
    }

    var response = cache.get('vyhladaj_osobu',
          query.meno,
          query.priezvisko,
          query.absolventi == "true",
          query.studenti == "true",
          query.zamestnanci == "true",
          query.akademickyRok,
          query.fakulta,
          query.skratkaSp,
          query.uchadzaciRocnik == "true",
          query.prvyRocnik == "true",
          query.druhyRocnik == "true",
          query.tretiRocnik == "true",
          query.stvrtyRocnik == "true",
          query.piatyRocnik == "true",
          query.siestyRocnik == "true",
          query.siedmyRocnik == "true",
          query.osmyRocnik == "true",
          query.absolventiRocnik == "true");

    if (!response) {
      return <Votr.Loading requests={cache.missing} />;
    }

    var [osoby, message] = response;

    var [osoby, header] = Votr.sortTable(
      osoby, Votr.RegisterOsobColumns, this.props.query, 'osobySort');

    if (!message && !osoby.length) {
      message = "Podmienkam nevyhovuje žiadny záznam.";
    }

    return <div>
      <h2>Výsledky</h2>
      <table className="table table-condensed table-bordered table-striped table-hover">
        <thead>{header}</thead>
        <tbody>
          {osoby.map((osoba, index) =>
            <tr key={index}>
              <td>{osoba.plne_meno}</td>
              <td>{osoba.email}</td>
            </tr>
          )}
        </tbody>
        {message && <tfoot><tr><td colSpan={Votr.RegisterOsobColumns.length}>{message}</td></tr></tfoot>}
      </table>
    </div>;
  }
});


Votr.RegisterOsobPage = React.createClass({
  render: function () {
    return <Votr.PageLayout query={this.props.query}>
        <Votr.PageTitle>Register osôb</Votr.PageTitle>
        <Votr.RegisterOsobForm query={this.props.query} />
        <Votr.RegisterOsobResultTable query={this.props.query} />
    </Votr.PageLayout>;
  }
});


})();
