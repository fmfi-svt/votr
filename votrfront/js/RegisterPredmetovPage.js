
import React from 'react';
import { CacheRequester, Loading } from './ajax';
import { currentAcademicYear } from './coursesStats';
import { classForSemester, humanizeBoolean } from './humanizeAISData';
import { FormItem, PageLayout, PageTitle } from './layout';
import { Link, navigate, queryConsumer } from './router';
import { sortAs, sortTable } from './sorting';


export var RegisterPredmetovColumns = [
  ["Názov predmetu", 'nazov'],
  ["Skratka predmetu", 'skratka'],
  ["Fakulta", 'fakulta'],
  [<abbr title="Semester">Sem.</abbr>, 'semester'],
  ["Rozsah výučby", 'rozsah_vyucby'],
  ["Počet kreditov", 'kredit', sortAs.number],
  ["Konanie", 'konanie']
];
RegisterPredmetovColumns.defaultOrder = 'a0';

export class RegisterPredmetovForm extends React.Component {
  constructor(props) {
    super(props);
    var query = props.query;
    this.state = {
      fakulta: query.fakulta,
      stredisko: query.stredisko,
      semester: query.semester,
      stupen: query.stupen,
      studijnyProgramSkratka: query.studijnyProgramSkratka,
      skratkaPredmetu: query.skratkaPredmetu,
      nazovPredmetu: query.nazovPredmetu,
      akademickyRok: query.akademickyRok || currentAcademicYear()
    };
  }

  handleFieldChange = (event) => {
    this.setState({ [event.target.name]: event.target.value });
  }

  handleSubmit = (event) => {
    event.preventDefault();
    navigate({ action: 'registerPredmetov', ...this.state });
  }

  renderTextInput(label, name, focus) {
    return <FormItem label={label}>
      <input className="form-item-control" name={name} autoFocus={focus}
             value={this.state[name] || ''} type="text" onChange={this.handleFieldChange} />
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
      <FormItem>
        <button className="btn btn-primary" type="submit">Vyhľadaj</button>
      </FormItem>
    </form>;
  }
}

export function RegisterPredmetovResultTable(props) {
  var cache = new CacheRequester();
  var query = props.query;
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
    return <Loading requests={cache.missing} />
  }

  var [rows, message] = response;

  var [rows, header] = sortTable(
    rows, RegisterPredmetovColumns, query, 'predmetSort');

  if (!message && !rows.length) {
    message = "Podmienkam nevyhovuje žiadny záznam.";
  }

  return (
    <React.Fragment>
      <h2>Výsledky</h2>
      <table className="table table-condensed table-bordered table-striped table-hover">
        <thead>{header}</thead>
        <tbody>
          {rows.map((predmet) =>
            <tr key={predmet.predmet_key} className={classForSemester(predmet.semester)}>
              <td><Link href={{ ...query, modal: 'detailPredmetu', modalPredmetKey: predmet.predmet_key, modalAkademickyRok: query.akademickyRok }}>
                {predmet.nazov}
              </Link></td>
              <td>{predmet.skratka}</td>
              <td>{predmet.fakulta}</td>
              <td>{predmet.semester}</td>
              <td>{predmet.rozsah_vyucby}</td>
              <td>{predmet.kredit}</td>
              <td>{humanizeBoolean(predmet.konanie)}</td>
            </tr>
          )}
        </tbody>
        {message && <tfoot><tr><td colSpan={RegisterPredmetovColumns.length}>{message}</td></tr></tfoot>}
      </table>
    </React.Fragment>
  );
}


export function RegisterPredmetovPage() {
  return queryConsumer(query => (
    <PageLayout>
      <div className="header">
        <PageTitle>Register predmetov</PageTitle>
      </div>
      <RegisterPredmetovForm query={query} />
      <RegisterPredmetovResultTable query={query} />
    </PageLayout>
  ));
}
