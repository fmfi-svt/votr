/** @jsx React.DOM */

(function () {


Votr.RegisterPredmetovForm = React.createClass({
  getInitialState: function () {
    var query = this.props.query

    return {
      fakulta: query.fakulta || '',
      stredisko: query.stredisko || '',
      studijnyProgramSkratka: query.studijnyProgramSkratka || '',
      skratkaPredmetu: query.skratkaPredmetu || '',
      nazovPredmetu: query.nazovPredmetu || '',
      akademickyRok: query.akademickyRok || '',
      semester: query.semester || '',
      stupen: query.stupen || ''
    };
  },

  render: function () {
    var cache = new Votr.CacheRequester();
    var fakulty = cache.get('get_register_predmetov_fakulta_options');
    var rocniky = cache.get('get_register_predmetov_akademicky_rok_options');
    var stupne = cache.get('get_register_predmetov_stupen_options');
    var semestre = cache.get('get_register_predmetov_semester_options');

    return <form onSubmit={this.handleSubmit}>
      <div>
        <label>
          {"Fakulta: "}
          {fakulty ? 
            <select name="fakulta" value={this.state.fakulta} onChange={this.handleFieldChange}>
              {fakulty.map((fakulta) =>
                <option key={fakulta.id} value={fakulta.id}>{fakulta.title}</option>
              )}
            </select> : <Votr.Loading requests={cache.missing} />}
        </label>
      </div>
      <div>
        <label>
          {"Stredisko: "}
          <input name="stredisko" value={this.state.stredisko} type="text" onChange={this.handleFieldChange} />
        </label>
      </div>
      <div>
        <label>
          {"Štúdijný program: "}
          <input name="studijnyProgramSkratka" value={this.state.studijnyProgram} type="text" onChange={this.handleFieldChange} />
        </label>
      </div>
      <div>
        <label>
          {"Skratka predmetu: "}
          <input name="skratkaPredmetu" value={this.state.skratkaPredmetu} type="text" onChange={this.handleFieldChange} />
        </label>
      </div>
      <div>
        <label>
          {"Názov predmetu: "}
          <input name="nazovPredmetu" value={this.state.nazovPredmetu} type="text" onChange={this.handleFieldChange} />
        </label>
      </div>
      <div>
        <label>
          {"Semester: "}
          {semestre ?
            <select name="semester" value={this.state.semester} onChange={this.handleFieldChange}>
              {semestre.map((semester) =>
                <option key={semester.id} value={semester.id}>{semester.title}</option>
              )}
            </select> : <Votr.Loading requests={cache.missing} />}
        </label>
      </div>
      <div>
        <label>
          {"Akademický rok: "}
          {rocniky ?
            <select name="akademickyRok" value={this.state.akademickyRok != '' ? this.state.akademickyRok : rocniky[1].id} onChange={this.handleFieldChange}>
              {rocniky[0].map((rocnik) =>
                <option key={rocnik.id} value={rocnik.id}>{rocnik.title}</option>
              )}
            </select> : <Votr.Loading requests={cache.missing} />}
        </label>
      </div>
      <div>
        <label>
          {"Stupeň: "}
          {stupne ? 
            <select name="stupen" value={this.state.stupen} onChange={this.handleFieldChange}>
              {stupne.map((stupen) =>
                <option key={stupen.id} value={stupen.id}>{stupen.title}</option>
              )}
            </select> : <Votr.Loading requests={cache.missing} />}
        </label>
      </div>
      <div>
        <button type="submit">Vyhľadaj</button>
      </div>
    </form>;
  },

  handleFieldChange: function (event) {
    var update = {};
    update[event.target.name] = event.target.value;
    this.setState(update);
  },

  handleSubmit: function(event) {
    var state = this.state;
    event.preventDefault();
    Votr.navigate(_.assign({ action: 'registerPredmetov' }, this.state));
  }
});

Votr.RegisterPredmetovResultTable = React.createClass({
  render: function () {
    var cache = new Votr.CacheRequester();
    var query = this.props.query
    if(query.fakulta == undefined &&
       query.stredisko == undefined &&
       query.studijnyProgramSkratka == undefined &&
       query.skratkaPredmetu == undefined &&
       query.nazovPredmetu == undefined &&
       query.akademickyRok == undefined &&
       query.semester == undefined &&
       query.stupen == undefined )
      return null;

    var response = cache.get('vyhladaj_predmety',
          query.fakulta || null,
          query.stredisko || null,
          query.studijnyProgramSkratka || null,
          query.skratkaPredmetu || null,
          query.nazovPredmetu || null,
          query.akademickyRok || null,
          query.semester || null,
          query.stupen || null);

    if(!response)
      return <Votr.Loading requests={cache.missing} />
    
    var [rows, message] = response;

    return <div>
        <div>{message}</div>
        <table>
          <tr>
            <th>Názov predmetu</th>
            <th>Fakulta</th>
            <th>Stredisko</th>
            <th>Skratka predmetu</th>
            <th>Typ výučby</th>
            <th>Semester</th>
            <th>Počet kreditov</th>
            <th>Konanie</th>
          </tr>
          { rows.map((predmet) =>         
          <tr key={predmet.skratka}>
            <td>{predmet.nazov}</td>
            <td>{predmet.fakulta}</td>
            <td>{predmet.stredisko}</td>
            <td>{predmet.skratka}</td>
            <td>{predmet.rozsah_vyucby}</td>
            <td>{predmet.semester}</td>
            <td>{predmet.kredit}</td>
            <td>{predmet.konanie}</td>
          </tr> )}
        </table>
    </div>;
  }
});


Votr.RegisterPredmetovPage = React.createClass({
  render: function () {
    return <Votr.PageLayout query={this.props.query}>
        <Votr.RegisterPredmetovForm query={this.props.query} />
        <Votr.RegisterPredmetovResultTable query={this.props.query} />
    </Votr.PageLayout>;
  }
});


})();
