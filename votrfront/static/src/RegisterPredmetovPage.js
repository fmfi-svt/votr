/** @jsx React.DOM */

(function () {


Votr.RegisterPredmetovForm = React.createClass({
  render: function () {
    var cache = new Votr.CacheRequester();
    var fakulty = cache.get('get_fakulta_options');
    var rocniky = cache.get('get_akademicky_rok_options');
    var stupne = cache.get('get_stupen_options');
    var semestre = cache.get('get_semester_options');

    if(!fakulty || !rocniky || !stupne || !semestre)
      return <Votr.Loading requests={cache.missing} />

    return <form onSubmit={this.handleSubmit}>
        <div>
          <label htmlFor="fakultaSelect">Fakulta: </label>
          {fakulty ?
            <select id="fakultaSelect" onChange={this.handleFieldChange}>
              {fakulty.map((fakulta, index) =>
              <option value={fakulta.id}>{fakulta.title}</option> )}
            </select> : <Votr.Loading requests={cache.missing} />}
        </div>
        <div>
          <label htmlFor="strediskoInput" onChange={this.handleFieldChange}>Stredisko: </label>
          <input id="strediskoInput" type="text" />
        </div>
        <div>
          <label htmlFor="studijnyProgramInput" onChange={this.handleFieldChange}>Štúdijný program: </label>
          <input id="studijnyProgramInput" type="text" />
        </div>
        <div>
          <label htmlFor="skratkaPredmetuInput" onChange={this.handleFieldChange}>Skratka predmetu: </label>
          <input id="skratkaPredmetuInput" type="text" />
        </div>
        <div>
          <label htmlFor="nazovPredmetuInput" onChange={this.handleFieldChange}>Názov predmetu: </label>
          <input id="nazovPredmetuInput" type="text" />
        </div>
        <div>
          <label htmlFor="semesterSelect">Semester: </label>
          {semestre ?
            <select id="semesterSelect" onChange={this.handleFieldChange}>
              {semestre.map((semester, index) =>
              <option value={semester.id}>{semester.title}</option> )})
            </select> : <Votr.Loading requests={cache.missing} />}
        </div>
        <div>
          <label htmlFor="akademickyRokSelect">Akademický rok: </label>
          {rocniky ?
            <select id="akademickyRokSelect" onChange={this.handleFieldChange}>
              {rocniky.map((rocnik, index) =>
              <option value={rocnik.id}>{rocnik.title}</option> )})
            </select> : <Votr.Loading requests={cache.missing} />}
        </div>
        <div>
          <label htmlFor="stupenSelect">Stupeň: </label>
          {stupne ?
            <select id="stupenSelect" onChange={this.handleFieldChange}>
              {stupne.map((stupen, index) => 
              <option value={stupen.id}>{stupen.title}</option> )})
            </select> : <Votr.Loading requests={cache.missing} />}
        </div>
        <div>
          <button type="submit">Vyhľadaj</button>
        </div>
    </form>;
  },
  handleFieldChange: function (event) {
    var update = {};
    update[event.target.id] = event.target.value;
    this.setState(update);
  },
  handleSubmit: function(event) {
    var state = this.state;
    event.preventDefault();
    Votr.navigate({ action: 'registerPredmetov', fakulta: state.fakultaSelect,
                    stredisko: state.strediskoInput, studijnyProgramSkratka: state.studijnyProgramInput,
                    skratkaPredmetu: state.skratkaPredmetuInput, nazovPredmetu: state.nazovPredmetuInput,
                    semester: state.semesterSelect, akademickyRok: state.akademickyRokSelect,
                    stupen: state.stupenSelect });
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
      return <div></div>;

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
    
    return <div>
        {response[1] != null ? <div>{ response[1] }</div> : ''}
        <table>
          <tr>
            <th>Názov predmetu</th>
            <th>Skratka predmetu</th>
            <th>Typ výučby</th>
            <th>Semester</th>
            <th>Počet kreditov</th>
          </tr>
          { response[0].map((predmet, index) =>
          <tr>
            <td>{predmet.nazov}</td>
            <td>{predmet.skratka}</td>
            <td>{predmet.typ_vyucby}</td>
            <td>{predmet.semester}</td>
            <td>{predmet.kredit}</td>
          </tr> )}
        </table>
    </div>;
  }
});


Votr.RegisterPredmetovPage = React.createClass({
  render: function () {
    return <Votr.PageLayout query={this.props.query}>
        <Votr.RegisterPredmetovForm query={this.props.query} component={Votr.RegisterPredmetovForm} />
        <Votr.RegisterPredmetovResultTable query={this.props.query} component={Votr.RegisterPredmetovResultTable} />
    </Votr.PageLayout>;
  }
});


})();
