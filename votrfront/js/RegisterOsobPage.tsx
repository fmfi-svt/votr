import React, { useContext, useState } from "react";
import { CacheRequester, Loading } from "./ajax";
import { currentAcademicYear } from "./coursesStats";
import { FormItem, PageLayout, PageTitle } from "./layout";
import { navigate, QueryContext } from "./router";
import { sortAs, sortTable } from "./sorting";
import { Columns, ComboBoxOption } from "./types";

export var RegisterOsobColumns: Columns = [
  ["Plné meno", "plne_meno", sortAs.personName],
  ["E-mail", "email"],
];
RegisterOsobColumns.defaultOrder = "a0";

export function RegisterOsobForm() {
  var query = useContext(QueryContext);

  var [state, setState] = useState(() => ({
    meno: query.meno,
    priezvisko: query.priezvisko,
    absolventi: query.absolventi,
    studenti: query.studenti,
    zamestnanci: query.zamestnanci,
    akademickyRok: query.akademickyRok || currentAcademicYear(),
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
    absolventiRocnik: query.absolventiRocnik,
  }));

  function handleFieldChange(
    event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) {
    var name = event.target.name;
    var value = event.target.value;
    setState((old) => ({ ...old, [name]: value }));
  }

  function handleCheckBoxChange(event: React.ChangeEvent<HTMLInputElement>) {
    var name = event.target.name;
    var value = String(event.target.checked);
    setState((old) => ({ ...old, [name]: value }));
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    navigate({ action: "registerOsob", ...state });
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
    items: ComboBoxOption[] | null
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

  function renderCheckbox(label: string, name: keyof typeof state) {
    return (
      <label>
        <input
          name={name}
          checked={state[name] == "true"}
          type="checkbox"
          onChange={handleCheckBoxChange}
        />
        {label}
      </label>
    );
  }

  var akademickeRoky = cache.get("get_register_osob_akademicky_rok_options");
  var fakulty = cache.get("get_register_osob_fakulty");

  return (
    <form onSubmit={handleSubmit}>
      {renderTextbox("Priezvisko: ", "priezvisko", true)}
      {renderTextbox("Meno: ", "meno")}
      {renderSelect("Fakulta: ", "fakulta", fakulty)}
      {renderTextbox("Študijný program (skratka): ", "skratkaSp")}
      {renderSelect("Akademický rok: ", "akademickyRok", akademickeRoky)}
      <div className="form-item">
        <div className="col-sm-4 form-item-label">Typ osoby:</div>
        <div className="col-sm-8">
          {renderCheckbox(" Absolventi ", "absolventi")}
          {renderCheckbox(" Študenti ", "studenti")}
          {renderCheckbox(" Zamestnanci ", "zamestnanci")}
        </div>
      </div>
      <div className="form-item">
        <div className="col-sm-4 form-item-label">Rok štúdia:</div>
        <div className="col-sm-8">
          {renderCheckbox(" 1. ", "prvyRocnik")}
          {renderCheckbox(" 2. ", "druhyRocnik")}
          {renderCheckbox(" 3. ", "tretiRocnik")}
          {renderCheckbox(" 4. ", "stvrtyRocnik")}
          {renderCheckbox(" 5. ", "piatyRocnik")}
          {renderCheckbox(" 6. ", "siestyRocnik")}
          {renderCheckbox(" 7. ", "siedmyRocnik")}
          {renderCheckbox(" 8. ", "osmyRocnik")}
          <br />
          {renderCheckbox(" Uchádzači ", "uchadzaciRocnik")}
          {renderCheckbox(" Absolventi ", "absolventiRocnik")}
        </div>
      </div>
      <FormItem>
        <button className="btn btn-primary" type="submit">
          Vyhľadaj
        </button>
      </FormItem>
    </form>
  );
}

export function RegisterOsobResultTable() {
  var query = useContext(QueryContext);
  var cache = new CacheRequester();

  if (
    !query.akademickyRok ||
    !(
      query.meno ||
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
      query.absolventiRocnik == "true"
    )
  ) {
    return null;
  }

  var response = cache.get(
    "vyhladaj_osobu",
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
    query.absolventiRocnik == "true"
  );

  if (!response) {
    return <Loading requests={cache.missing} />;
  }

  var [osoby, message] = response;

  var [osoby, header] = sortTable(
    osoby,
    RegisterOsobColumns,
    query,
    "osobySort"
  );

  if (!message && !osoby.length) {
    message = "Podmienkam nevyhovuje žiadny záznam.";
  }

  return (
    <React.Fragment>
      <h2>Výsledky</h2>
      <table className="table table-condensed table-bordered table-striped table-hover">
        <thead>{header}</thead>
        <tbody>
          {osoby.map((osoba, index) => (
            <tr key={index}>
              <td>{osoba.plne_meno}</td>
              <td>
                {osoba.email && (
                  <a href={"mailto:" + osoba.email}>{osoba.email}</a>
                )}
              </td>
            </tr>
          ))}
        </tbody>
        {message && (
          <tfoot>
            <tr>
              <td colSpan={RegisterOsobColumns.length}>{message}</td>
            </tr>
          </tfoot>
        )}
      </table>
    </React.Fragment>
  );
}

export function makeRegisterOsobPage() {
  return (
    <PageLayout>
      <div className="header">
        <PageTitle>Register osôb</PageTitle>
      </div>
      <RegisterOsobForm />
      <RegisterOsobResultTable />
    </PageLayout>
  );
}
