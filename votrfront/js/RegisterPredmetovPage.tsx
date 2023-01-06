import React, { useContext, useState } from "react";
import { CacheRequester, Loading } from "./ajax";
import { currentAcademicYear } from "./coursesStats";
import { classForSemester, humanizeBoolean } from "./humanizeAISData";
import { FormItem, PageLayout, PageTitle } from "./layout";
import { navigate, QueryContext, RelativeLink } from "./router";
import { sortAs, sortTable } from "./sorting";
import { Columns, ComboBoxOption } from "./types";

var RegisterPredmetovColumns: Columns = [
  ["Názov predmetu", "nazov"],
  ["Skratka predmetu", "skratka"],
  ["Fakulta", "fakulta"],
  [<abbr title="Semester">Sem.</abbr>, "semester"],
  ["Rozsah výučby", "rozsah_vyucby"],
  ["Počet kreditov", "kredit", sortAs.number],
  ["Konanie", "konanie"],
];
RegisterPredmetovColumns.defaultOrder = "a0";

function RegisterPredmetovForm() {
  var query = useContext(QueryContext);

  var [state, setState] = useState(() => ({
    fakulta: query.fakulta,
    stredisko: query.stredisko,
    semester: query.semester,
    stupen: query.stupen,
    studijnyProgramSkratka: query.studijnyProgramSkratka,
    skratkaPredmetu: query.skratkaPredmetu,
    nazovPredmetu: query.nazovPredmetu,
    akademickyRok: query.akademickyRok || currentAcademicYear(),
  }));

  function handleFieldChange(
    event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) {
    var name = event.target.name;
    var value = event.target.value;
    setState((old) => ({ ...old, [name]: value }));
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    navigate({ action: "registerPredmetov", ...state });
  }

  var cache = new CacheRequester();

  function renderTextbox(
    label: string,
    name: keyof typeof state,
    focus: boolean = false
  ) {
    return (
      <FormItem label={label}>
        <input
          className="form-item-control"
          name={name}
          autoFocus={focus}
          value={state[name] || ""}
          type="text"
          onChange={handleFieldChange}
        />
      </FormItem>
    );
  }

  function renderSelect(
    label: string,
    name: keyof typeof state,
    items: ComboBoxOption[] | undefined
  ) {
    return (
      <FormItem label={label}>
        {items ? (
          <select
            className="form-item-control"
            name={name}
            value={state[name]}
            onChange={handleFieldChange}
          >
            {items.map((item) => (
              <option key={item.id} value={item.id}>
                {item.title}
              </option>
            ))}
          </select>
        ) : (
          <Loading requests={cache.missing} />
        )}
      </FormItem>
    );
  }

  var fakulty = cache.get("get_register_predmetov_fakulta_options");
  var rocniky = cache.get("get_register_predmetov_akademicky_rok_options");
  var stupne = cache.get("get_register_predmetov_stupen_options");
  var semestre = cache.get("get_register_predmetov_semester_options");

  return (
    <form onSubmit={handleSubmit}>
      {renderTextbox("Názov predmetu: ", "nazovPredmetu", true)}
      {renderTextbox("Skratka predmetu: ", "skratkaPredmetu")}
      {renderTextbox("Študijný program (skratka): ", "studijnyProgramSkratka")}
      {renderSelect("Fakulta: ", "fakulta", fakulty)}
      {renderTextbox("Stredisko: ", "stredisko")}
      {renderSelect("Stupeň: ", "stupen", stupne)}
      {renderSelect("Akademický rok: ", "akademickyRok", rocniky)}
      {renderSelect("Semester: ", "semester", semestre)}
      <FormItem>
        <button className="btn btn-primary" type="submit">
          Vyhľadaj
        </button>
      </FormItem>
    </form>
  );
}

function RegisterPredmetovResultTable() {
  var query = useContext(QueryContext);
  var cache = new CacheRequester();

  if (
    !query.fakulta &&
    !query.stredisko &&
    !query.studijnyProgramSkratka &&
    !query.skratkaPredmetu &&
    !query.nazovPredmetu &&
    !query.semester &&
    !query.stupen
  ) {
    return null;
  }

  if (!query.akademickyRok) {
    return null;
  }

  var response = cache.get(
    "vyhladaj_predmety",
    query.akademickyRok,
    query.fakulta || null,
    query.stredisko || null,
    query.studijnyProgramSkratka || null,
    query.skratkaPredmetu || null,
    query.nazovPredmetu || null,
    query.semester || null,
    query.stupen || null
  );

  if (!response) {
    return <Loading requests={cache.missing} />;
  }

  var [rows, message] = response;

  var [rows, header] = sortTable(
    rows,
    RegisterPredmetovColumns,
    query,
    "predmetSort"
  );

  if (!message && !rows.length) {
    message = "Podmienkam nevyhovuje žiadny záznam.";
  }

  return (
    <React.Fragment>
      <h2>Výsledky</h2>
      <table className="table table-condensed table-bordered table-striped table-hover">
        <thead>{header}</thead>
        <tbody>
          {rows.map((predmet) => (
            <tr
              key={predmet.predmet_key}
              className={classForSemester(predmet.semester)}
            >
              <td>
                <RelativeLink
                  href={{
                    modal: "detailPredmetu",
                    modalPredmetKey: predmet.predmet_key,
                    modalAkademickyRok: query.akademickyRok,
                  }}
                >
                  {predmet.nazov}
                </RelativeLink>
              </td>
              <td>{predmet.skratka}</td>
              <td>{predmet.fakulta}</td>
              <td>{predmet.semester}</td>
              <td>{predmet.rozsah_vyucby}</td>
              <td>{predmet.kredit}</td>
              <td>{humanizeBoolean(predmet.konanie)}</td>
            </tr>
          ))}
        </tbody>
        {!!message && (
          <tfoot>
            <tr>
              <td colSpan={RegisterPredmetovColumns.length}>{message}</td>
            </tr>
          </tfoot>
        )}
      </table>
    </React.Fragment>
  );
}

export function makeRegisterPredmetovPage() {
  return (
    <PageLayout>
      <div className="header">
        <PageTitle>Register predmetov</PageTitle>
      </div>
      <RegisterPredmetovForm />
      <RegisterPredmetovResultTable />
    </PageLayout>
  );
}
