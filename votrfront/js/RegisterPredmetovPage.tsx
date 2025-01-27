import React, { useContext, useState } from "react";
import { CacheRequester, Loading } from "./ajax";
import { currentAcademicYear } from "./coursesStats";
import { classForSemester, humanizeBoolean } from "./humanizeAISData";
import { FormItem, PageLayout, PageTitle } from "./layout";
import { underSM, underXS } from "./mediaQueries";
import { navigate, QueryContext, RelativeLink } from "./router";
import { column, SortableTable, sortAs } from "./sorting";
import type { ComboBoxOption, RegPredmet } from "./types";

function DetailPredmetuLink({ predmet }: { predmet: RegPredmet }) {
  const query = useContext(QueryContext);
  return (
    <RelativeLink
      href={{
        modal: "detailPredmetu",
        modalPredmetKey: predmet.predmet_key,
        modalAkademickyRok: query.akademickyRok,
      }}
    >
      {predmet.nazov}
    </RelativeLink>
  );
}

const registerPredmetovColumns = [
  column({
    label: "Názov predmetu",
    sortKey: (predmet: RegPredmet) => predmet.nazov,
    display: (predmet: RegPredmet) => <DetailPredmetuLink predmet={predmet} />,
    expansionMark: true,
  }),
  column({ label: "Skratka predmetu", prop: "skratka" }),
  column({ label: "Fakulta", prop: "fakulta", hide: underSM }),
  column({ label: <abbr title="Semester">Sem.</abbr>, prop: "semester" }),
  column({ label: "Rozsah výučby", prop: "rozsah_vyucby", hide: underXS }),
  column({
    label: "Počet kreditov",
    prop: "kredit",
    sortKey: sortAs.number,
    hide: underXS,
  }),
  column({
    label: "Konanie",
    prop: "konanie",
    display: humanizeBoolean,
    hide: underXS,
  }),
];

const registerPredmetovDefaultOrder = "a0";

function RegisterPredmetovForm() {
  const query = useContext(QueryContext);

  const [state, setState] = useState(() => ({
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
    event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) {
    const name = event.target.name;
    const value = event.target.value;
    setState((old) => ({ ...old, [name]: value }));
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    navigate({ action: "registerPredmetov", ...state });
  }

  const cache = new CacheRequester();

  function renderTextbox(
    label: string,
    name: keyof typeof state,
    focus: boolean = false,
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
    items: ComboBoxOption[] | undefined,
  ) {
    return (
      <FormItem label={label}>
        {items ?
          <select
            className="form-item-control"
            name={name}
            value={state[name]}
            onChange={handleFieldChange}
          >
            {items.map((item, index) => (
              <option key={index} value={item.id}>
                {item.title}
              </option>
            ))}
          </select>
        : <Loading requests={cache.missing} />}
      </FormItem>
    );
  }

  const fakulty = cache.get("get_register_predmetov_fakulta_options");
  const rocniky = cache.get("get_register_predmetov_akademicky_rok_options");
  const stupne = cache.get("get_register_predmetov_stupen_options");
  const semestre = cache.get("get_register_predmetov_semester_options");

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
  const query = useContext(QueryContext);
  const cache = new CacheRequester();

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

  const response = cache.get(
    "vyhladaj_predmety",
    query.akademickyRok,
    query.fakulta || null,
    query.stredisko || null,
    query.studijnyProgramSkratka || null,
    query.skratkaPredmetu || null,
    query.nazovPredmetu || null,
    query.semester || null,
    query.stupen || null,
  );

  if (!response) {
    return <Loading requests={cache.missing} />;
  }

  const [rows, serverMessage] = response;

  const message =
    serverMessage ||
    (rows.length ? null : "Podmienkam nevyhovuje žiadny záznam.");

  return (
    <React.Fragment>
      <h2>Výsledky</h2>
      <SortableTable
        items={rows}
        columns={registerPredmetovColumns}
        defaultOrder={registerPredmetovDefaultOrder}
        queryKey="predmetSort"
        message={message}
        rowClassName={(predmet) => classForSemester(predmet.semester)}
      />
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
