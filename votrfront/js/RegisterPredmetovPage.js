(function () {


Votr.RegisterPredmetovColumns = [
  ["Názov predmetu", 'nazov'],
  ["Skratka predmetu", 'skratka'],
  ["Fakulta", 'fakulta'],
  [<abbr title="Semester">Sem.</abbr>, 'semester'],
  ["Rozsah výučby", 'rozsah_vyucby'],
  ["Počet kreditov", 'kredit', Votr.sortAs.number],
  ["Konanie", 'konanie']
];
Votr.RegisterPredmetovColumns.defaultOrder = 'a0';

Votr.RegisterPredmetovForm = React.createClass({
  getInitialState: function () {
    var query = this.props.query;
    return {
      fakulta: query.fakulta,
      stredisko: query.stredisko,
      semester: query.semester,
      stupen: query.stupen,
      studijnyProgramSkratka: query.studijnyProgramSkratka,
      skratkaPredmetu: query.skratkaPredmetu,
      nazovPredmetu: query.nazovPredmetu,
      akademickyRok: query.akademickyRok || Votr.currentAcademicYear()
    };
  },

  handleFieldChange: function (event) {
    this.setState(_.zipObject([[event.target.name, event.target.value]]));
  },

  handleSubmit: function(event) {
    event.preventDefault();
    Votr.navigate(_.assign({ action: 'registerPredmetov' }, this.state));
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

  render: function () {
    var cache = new Votr.CacheRequester();
    var fakulty = cache.get('get_register_predmetov_fakulta_options');
    var rocniky = cache.get('get_register_predmetov_akademicky_rok_options');
    var stupne = cache.get('get_register_predmetov_stupen_options');
    var semestre = cache.get('get_register_predmetov_semester_options');

    return <form onSubmit={this.handleSubmit}>
      {this.renderTextInput("Názov predmetu: ", "nazovPredmetu", true)}
      {this.renderTextInput("Skratka predmetu: ", "skratkaPredmetu", false)}
      {this.renderTextInput("Študijný program (skratka): ", "studijnyProgramSkratka", false)}
      {this.renderSelect("Fakulta: ", "fakulta", fakulty, cache)}
      {this.renderTextInput("Stredisko: ", "stredisko", false)}
      {this.renderSelect("Stupeň: ", "stupen", stupne, cache)}
      {this.renderSelect("Akademický rok: ", "akademickyRok", rocniky, cache)}
      {this.renderSelect("Semester: ", "semester", semestre, cache)}
      <Votr.FormItem>
        <button className="btn btn-primary" type="submit">Vyhľadaj</button>
      </Votr.FormItem>
    </form>;
  }
});

Votr.RegisterPredmetovResultTable = React.createClass({
  render: function () {
    var cache = new Votr.CacheRequester();
    var query = this.props.query;
    if(!query.fakulta &&
       !query.stredisko &&
       !query.studijnyProgramSkratka &&
       !query.skratkaPredmetu &&
       !query.nazovPredmetu &&
       !query.semester &&
       !query.stupen) {
      return null;
    }

    if (!query.akademickyRok) {
      return null;
    }

    var response = cache.get('vyhladaj_predmety',
          query.akademickyRok,
          query.fakulta || null,
          query.stredisko || null,
          query.studijnyProgramSkratka || null,
          query.skratkaPredmetu || null,
          query.nazovPredmetu || null,
          query.semester || null,
          query.stupen || null);

    if (!response) {
      return <Votr.Loading requests={cache.missing} />
    }

    var [rows, message] = response;

    var [rows, header] = Votr.sortTable(
      rows, Votr.RegisterPredmetovColumns, this.props.query, 'predmetSort');

    if (!message && !rows.length) {
      message = "Podmienkam nevyhovuje žiadny záznam.";
    }

    return <div>
      <h2>Výsledky</h2>
      <table className="table table-condensed table-bordered table-striped table-hover">
        <thead>{header}</thead>
        <tbody>
          {rows.map((predmet) =>
            <tr key={predmet.predmet_key} className={Votr.classForSemester(predmet.semester)}>
              <td><Votr.Link href={_.assign({}, this.props.query, { modal: 'detailPredmetu', modalPredmetKey: predmet.predmet_key, modalAkademickyRok: query.akademickyRok })}>
                {predmet.nazov}
              </Votr.Link></td>
              <td>{predmet.skratka}</td>
              <td>{predmet.fakulta}</td>
              <td>{predmet.semester}</td>
              <td>{predmet.rozsah_vyucby}</td>
              <td>{predmet.kredit}</td>
              <td>{Votr.humanizeBoolean(predmet.konanie)}</td>
            </tr>
          )}
        </tbody>
        {message && <tfoot><tr><td colSpan={Votr.RegisterPredmetovColumns.length}>{message}</td></tr></tfoot>}
      </table>
    </div>;
  }
});


Votr.RegisterPredmetovPage = React.createClass({
  render: function () {
    return <Votr.PageLayout query={this.props.query}>
        <Votr.PageTitle>Register predmetov</Votr.PageTitle>
        <Votr.RegisterPredmetovForm query={this.props.query} />
        <Votr.RegisterPredmetovResultTable query={this.props.query} />
    </Votr.PageLayout>;
  }
});


})();
