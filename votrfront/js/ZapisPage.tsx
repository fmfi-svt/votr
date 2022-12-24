import PropTypes from "prop-types";
import React, { useContext, useState } from "react";
import _ from "lodash";
import { ZapisnyListSelector } from "./ZapisnyListSelector";
import { CacheRequester, Loading, RequestCache, sendRpc } from "./ajax";
import { coursesStats } from "./coursesStats";
import { humanizeTypVyucby, plural } from "./humanizeAISData";
import { FormItem, PageLayout, PageTitle } from "./layout";
import { Link, navigate, QueryContext } from "./router";
import { sortAs, SortableTable } from "./sorting";
import { Columns } from "./types";

const typVyucbyColumn = {
  label: <abbr title="Typ výučby">Typ</abbr>,
  prop: "typ_vyucby",
  cell: (predmet) => (
    <abbr title={humanizeTypVyucby(predmet.typ_vyucby)}>
      {predmet.typ_vyucby}
    </abbr>
  ),
};
const skratkaColumn = {
  label: "Skratka predmetu",
  prop: "skratka",
  hiddenClass: ["hidden-xs", "hidden-sm"],
};
const semesterColumn = {
  label: "Semester",
  shortLabel: <abbr title="Semester">Sem.</abbr>,
  prop: "semester",
  preferDesc: true,
};
const rozsahVyucbyColumn = {
  label: "Rozsah výučby",
  prop: "rozsah_vyucby",
  hiddenClass: ["hidden-xs", "hidden-sm"],
};
const kreditColumn = {
  label: "Kredit",
  prop: "kredit",
  process: sortAs.number,
  hiddenClass: ["hidden-xs"],
};
const prihlaseniColumn = {
  label: "Prihlásení",
  prop: "pocet_prihlasenych",
  process: sortAs.number,
  cell: (predmet) => (
    <React.Fragment>
      {RequestCache["pocet_prihlasenych_je_stary" + predmet.predmet_key] ? (
        <del>{predmet.pocet_prihlasenych}</del>
      ) : (
        predmet.pocet_prihlasenych
      )}
      {predmet.maximalne_prihlasenych && "/" + predmet.maximalne_prihlasenych}
    </React.Fragment>
  ),
  hiddenClass: ["hidden-xs"],
};
const jazykColumn = {
  label: "Jazyk",
  prop: "jazyk",
  cell: (predmet) => predmet.jazyk.replace(/ ,/g, ", "),
  hiddenClass: ["hidden-xs", "hidden-sm"],
};

export var ZapisZPlanuColumns: Columns = [
  typVyucbyColumn,
  {
    label: "Blok",
    process: (predmet) =>
      parseInt(predmet.blok_index || 0) * 1000 +
      parseInt(predmet.v_bloku_index || 0),
    hiddenClass: ["hidden-xs", "hidden-sm"],
    cell: (predmet) =>
      predmet.blok_nazov ? (
        <abbr title={predmet.blok_nazov}>{predmet.blok_skratka}</abbr>
      ) : (
        predmet.blok_skratka
      ),
  },
  skratkaColumn,
  semesterColumn,
  rozsahVyucbyColumn,
  kreditColumn,
  prihlaseniColumn,
  {
    label: <abbr title="Odporúčaný ročník">Odp. ročník</abbr>,
    prop: "odporucany_rocnik",
    hiddenClass: ["hidden-xs", "hidden-sm"],
  },
  jazykColumn,
];
ZapisZPlanuColumns.defaultOrder = "a1a2a9a3";

export var ZapisZPonukyColumns: Columns = [
  typVyucbyColumn,
  {
    label: "Blok",
    prop: "blok_skratka",
    hiddenClass: ["hidden-xs", "hidden-sm"],
  },
  skratkaColumn,
  semesterColumn,
  rozsahVyucbyColumn,
  kreditColumn,
  prihlaseniColumn,
  jazykColumn,
];
ZapisZPonukyColumns.defaultOrder = "a3";

export var ZapisVlastnostiColumns = [
  { label: "Skratka", prop: "skratka", expansionMark: true },
  { label: "Názov", prop: "nazov" },
  { label: "Minimálny kredit", prop: "minimalny_kredit" },
  { label: "Poznámka", prop: "poznamka" },
];

function ZapisLink(props) {
  return (
    <Link
      className={"btn btn-default" + (props.active ? " active" : "")}
      href={props.href}
    >
      {props.label}
    </Link>
  );
}

export function ZapisMenu() {
  var { action, cast, zapisnyListKey } = useContext(QueryContext);
  return (
    <div className="header">
      <PageTitle>Zápis predmetov</PageTitle>
      <div className="pull-right">
        <div className="btn-group">
          <ZapisLink
            label="Môj študijný plán"
            href={{ action: "zapisZPlanu", cast: "SC", zapisnyListKey }}
            active={action == "zapisZPlanu" && cast != "SS"}
          />
          <ZapisLink
            label="Predmety štátnej skúšky"
            href={{ action: "zapisZPlanu", cast: "SS", zapisnyListKey }}
            active={action == "zapisZPlanu" && cast == "SS"}
          />
          <ZapisLink
            label="Hľadať ďalšie predmety"
            href={{ action: "zapisZPonuky", zapisnyListKey }}
            active={action == "zapisZPonuky"}
          />
        </div>
      </div>
    </div>
  );
}

export function ZapisTableFooter(props: {
  predmety: Record<string, any>;
  moje: Record<string, boolean>;
  fullTable: boolean;
}) {
  var bloky = {},
    nazvy = {},
    semestre = {};
  for (const predmet of Object.values(props.predmety)) {
    semestre[predmet.semester] = true;
    if (predmet.blok_skratka) nazvy[predmet.blok_skratka] = predmet.blok_nazov;
  }

  for (const skratka of _.sortBy(_.keys(nazvy))) bloky[skratka] = [];
  bloky[""] = [];

  for (const predmet of Object.values(props.predmety)) {
    if (!props.moje[predmet.predmet_key]) continue;
    if (predmet.blok_skratka) bloky[predmet.blok_skratka].push(predmet);
    bloky[""].push(predmet);
  }

  var jedinySemester = _.keys(semestre).length <= 1;

  return (
    <React.Fragment>
      {_.map(bloky, (blok, skratka) => {
        var stats = coursesStats(blok);
        return (
          <React.Fragment key={skratka}>
            <tr
              key={skratka}
              className={props.fullTable ? null : "hidden-xs hidden-sm"}
            >
              <td colSpan={2}>{skratka ? "Súčet bloku" : "Dokopy"}</td>
              <td>
                {nazvy[skratka] ? (
                  <abbr title={nazvy[skratka]}>{skratka}</abbr>
                ) : (
                  skratka
                )}
              </td>
              <td colSpan={4}>
                {stats.spolu.count}{" "}
                {plural(stats.spolu.count, "predmet", "predmety", "predmetov")}
                {!jedinySemester &&
                  ` (${stats.zima.count} v zime, ${stats.leto.count} v lete)`}
              </td>
              <td>
                {stats.spolu.creditsEnrolled}
                {!jedinySemester &&
                  ` (${stats.zima.creditsEnrolled}+${stats.leto.creditsEnrolled})`}
              </td>
              <td colSpan={3}></td>
            </tr>
            <tr key={skratka + "sm"} className={"hidden-md hidden-lg"}>
              <td>{skratka ? "Súčet bloku" : "Dokopy"}</td>
              <td>
                {nazvy[skratka] ? (
                  <abbr title={nazvy[skratka]}>{skratka}</abbr>
                ) : (
                  skratka
                )}
              </td>
              <td colSpan={2}>
                {stats.spolu.count}{" "}
                {plural(stats.spolu.count, "predmet", "predmety", "predmetov")}
                {!jedinySemester &&
                  ` (${stats.zima.count} v zime, ${stats.leto.count} v lete)`}
                <span className="hidden-sm">
                  {", "}
                  {stats.spolu.creditsEnrolled}
                  {!jedinySemester &&
                    ` (${stats.zima.creditsEnrolled}+${stats.leto.creditsEnrolled})`}{" "}
                  {plural(
                    stats.spolu.creditsEnrolled,
                    "kredit",
                    "kredity",
                    "kreditov"
                  )}
                </span>
              </td>
              <td colSpan={2} className="hidden-xs">
                {stats.spolu.creditsEnrolled}
                {!jedinySemester &&
                  ` (${stats.zima.creditsEnrolled}+${stats.leto.creditsEnrolled})`}
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
  moje: PropTypes.object.isRequired,
};

export function ZapisTable(props) {
  var query = useContext(QueryContext);
  var [saving, setSaving] = useState(false);
  var [changes, setChanges] = useState({});

  var predmety = props.predmety;

  function handleChange(event) {
    var predmetKey = event.target.name;
    var predmet = predmety[predmetKey];

    // prettier-ignore
    var want =
      predmet.moje && !event.target.checked ? false :
      !predmet.moje && event.target.checked ? true :
      undefined;
    setChanges((changes) => ({ ...changes, [predmetKey]: want }));
  }

  function handleSave(event) {
    event.preventDefault();

    if (saving) return;

    var odoberanePredmety = [],
      pridavanePredmety = [];
    for (var predmet_key in predmety) {
      if (changes[predmet_key] === false && predmety[predmet_key].moje) {
        odoberanePredmety.push(predmety[predmet_key]);
      }
      if (changes[predmet_key] === true && !predmety[predmet_key].moje) {
        pridavanePredmety.push(predmety[predmet_key]);
      }
    }

    setSaving(true);

    var koniec = (odobral, pridal) => {
      setSaving(false);

      if (odobral) {
        for (const predmet of odoberanePredmety) {
          RequestCache["pocet_prihlasenych_je_stary" + predmet.predmet_key] =
            true;
        }
        setChanges((changes) => _.pickBy(changes, (value) => value === true));
      }

      if (pridal) {
        for (const predmet of pridavanePredmety) {
          RequestCache["pocet_prihlasenych_je_stary" + predmet.predmet_key] =
            true;
        }
        setChanges((changes) => _.pickBy(changes, (value) => value === false));
      }

      // Aj ked skoncime neuspechom, je mozne, ze niektore predmety sa zapisali.
      RequestCache.invalidate("get_hodnotenia");
      RequestCache.invalidate("get_predmety");
      RequestCache.invalidate("get_prehlad_kreditov");
      RequestCache.invalidate("get_studenti_zapisani_na_predmet");
      RequestCache.invalidate("zapis_get_zapisane_predmety");
    };

    props.odoberPredmety(odoberanePredmety, (message) => {
      if (message) {
        alert(message);
        koniec(false, false);
      } else {
        props.pridajPredmety(pridavanePredmety, (message) => {
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

  // Chceme, aby sa pre ZapisTable zachoval state aj vtedy, ked tabulku
  // nevidno, lebo sme prave zapisali predmety a obnovujeme zoznam predmetov.
  // Takze komponent ZapisTable sa bude renderovat vzdy, aby nikdy nezanikol
  // a neprisiel o state. Niekedy proste dostane predmety == undefined.
  if (!predmety || !props.akademickyRok) {
    return <span />;
  }

  var classes = {},
    checked = {};
  for (var predmet_key in predmety) {
    checked[predmet_key] = predmety[predmet_key].moje;
    if (changes[predmet_key] === false && predmety[predmet_key].moje) {
      classes[predmet_key] = "danger";
      checked[predmet_key] = false;
    }
    if (changes[predmet_key] === true && !predmety[predmet_key].moje) {
      classes[predmet_key] = "success";
      checked[predmet_key] = true;
    }
  }

  var saveButton = (
    <div className="section">
      <button
        type="submit"
        className="btn btn-primary"
        disabled={_.isEmpty(classes)}
      >
        {saving ? <Loading /> : "Uložiť zmeny"}
      </button>
    </div>
  );

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
        onChange={handleChange}
      />
    ),
  };

  // nazovColumn
  const nazovColumn = {
    label: "Názov predmetu",
    prop: "nazov",
    expansionMark: true,
    cell: (predmet) => {
      var href = {
        ...query,
        modal: "detailPredmetu",
        modalPredmetKey: predmet.predmet_key,
        modalAkademickyRok: props.akademickyRok,
      };
      var nazov = <Link href={href}>{predmet.nazov}</Link>;
      if (predmet.moje) nazov = <strong>{nazov}</strong>;
      if (predmet.aktualnost) {
        nazov = (
          <React.Fragment>
            <del>{nazov}</del> (nekoná sa)
          </React.Fragment>
        );
      }
      return nazov;
    },
  };
  var columns = [
    mojeColumn,
    ...props.columns.slice(0, 2),
    nazovColumn,
    ...props.columns.slice(2),
  ];

  const footer = (fullTable) =>
    props.showFooter && (
      <ZapisTableFooter
        predmety={predmety}
        moje={checked}
        fullTable={fullTable}
      />
    );

  return (
    <form onSubmit={handleSave}>
      {saveButton}
      <SortableTable
        items={_.values(predmety)}
        columns={columns}
        queryKey="predmetySort"
        footer={footer}
        message={props.message}
      />
      {saveButton}
    </form>
  );
}

ZapisTable.propTypes = {
  predmety: PropTypes.object,
  akademickyRok: PropTypes.string,
  message: PropTypes.node,
  columns: PropTypes.array.isRequired,
  showFooter: PropTypes.bool,
  odoberPredmety: PropTypes.func.isRequired,
  pridajPredmety: PropTypes.func.isRequired,
};

export function ZapisVlastnostiTable() {
  var { zapisnyListKey } = useContext(QueryContext);
  var cache = new CacheRequester();

  var [vlastnosti, message] =
    cache.get("zapis_get_vlastnosti_programu", zapisnyListKey) || [];

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

export function ZapisZPlanuPageContent() {
  var query = useContext(QueryContext);
  var { zapisnyListKey, cast } = query;
  cast = cast == "SS" ? "SS" : "SC";

  var cache = new CacheRequester();

  var [zapisanePredmety, zapisaneMessage] =
    cache.get("zapis_get_zapisane_predmety", zapisnyListKey, cast) || [];
  var [ponukanePredmety, ponukaneMessage] =
    cache.get("zapis_plan_vyhladaj", zapisnyListKey, cast) || [];
  var akademickyRok = cache.get(
    "zapisny_list_key_to_akademicky_rok",
    zapisnyListKey
  );

  var outerMessage, tableMessage, predmety;

  if (zapisaneMessage || ponukaneMessage) {
    outerMessage = <p>{zapisaneMessage || ponukaneMessage}</p>;
  } else if (!cache.loadedAll) {
    outerMessage = <Loading requests={cache.missing} />;
  } else {
    var vidnoZimne = false;

    predmety = {};
    for (const predmet of ponukanePredmety) {
      predmety[predmet.predmet_key] = { moje: false, ...predmet };
      if (predmet.semester == "Z") vidnoZimne = true;
    }
    for (const predmet of zapisanePredmety) {
      var predmet_key = predmet.predmet_key;
      if (!predmety[predmet_key]) {
        if (predmet.semester == "Z" && !vidnoZimne) continue;
        predmety[predmet_key] = { moje: true, ...predmet };
      } else {
        for (var property in predmet) {
          if (predmet[property] !== null && predmet[property] !== undefined) {
            predmety[predmet_key][property] = predmet[property];
          }
        }
        predmety[predmet_key].moje = true;
      }
    }

    if (_.isEmpty(predmety)) {
      tableMessage = "Zoznam ponúkaných predmetov je prázdny.";
    }
  }

  return (
    <React.Fragment>
      <ZapisMenu />
      {outerMessage}
      <ZapisTable
        predmety={predmety}
        message={tableMessage}
        akademickyRok={akademickyRok}
        odoberPredmety={odoberPredmety}
        pridajPredmety={pridajPredmety}
        columns={ZapisZPlanuColumns}
        showFooter={true}
      />
      <h2>Poznámky k študijnému plánu</h2>
      <ZapisVlastnostiTable />
    </React.Fragment>
  );

  function pridajPredmety(predmety, callback) {
    if (!predmety.length) return callback(null);

    var dvojice = predmety.map((predmet) => [
      predmet.typ_vyucby,
      predmet.skratka,
    ]);
    sendRpc(
      "zapis_plan_pridaj_predmety",
      [zapisnyListKey, cast, dvojice],
      callback
    );
  }

  function odoberPredmety(predmety, callback) {
    if (!predmety.length) return callback(null);

    var kluce = predmety.map((predmet) => predmet.predmet_key);
    sendRpc("zapis_odstran_predmety", [zapisnyListKey, cast, kluce], callback);
  }
}

export function makeZapisZPlanuPage() {
  return (
    <PageLayout>
      <ZapisnyListSelector>
        <ZapisZPlanuPageContent />
      </ZapisnyListSelector>
    </PageLayout>
  );
}

export function ZapisZPonukyForm() {
  var query = useContext(QueryContext);

  var [state, setState] = useState({
    fakulta: query.fakulta,
    stredisko: query.stredisko,
    skratkaPredmetu: query.skratkaPredmetu,
    nazovPredmetu: query.nazovPredmetu,
  });

  function handleFieldChange(event) {
    var name = event.target.name;
    var value = event.target.value;
    setState((old) => ({ ...old, [name]: value }));
  }

  function handleSubmit(event) {
    event.preventDefault();
    navigate({
      action: "zapisZPonuky",
      zapisnyListKey: query.zapisnyListKey,
      ...state,
    });
  }

  var cache = new CacheRequester();

  function renderTextbox(label, name, focus = false) {
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

  function renderSelect(label, name, items) {
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

  var [fakulty, message] =
    cache.get("zapis_ponuka_options", query.zapisnyListKey) || [];

  if (!fakulty) {
    return <Loading requests={cache.missing} />;
  }

  if (message) {
    return <p>{message}</p>;
  }

  return (
    <form onSubmit={handleSubmit}>
      {renderTextbox("Názov predmetu: ", "nazovPredmetu", true)}
      {renderTextbox("Skratka predmetu: ", "skratkaPredmetu")}
      {renderSelect("Fakulta: ", "fakulta", fakulty)}
      {renderTextbox("Stredisko: ", "stredisko")}
      <FormItem>
        <button className="btn btn-primary" type="submit">
          Vyhľadaj
        </button>
      </FormItem>
    </form>
  );
}

export function ZapisZPonukyPageContent() {
  var query = useContext(QueryContext);
  var cache = new CacheRequester();

  var outerMessage, tableMessage, predmety, akademickyRok;

  if (
    query.fakulta ||
    query.stredisko ||
    query.skratkaPredmetu ||
    query.nazovPredmetu
  ) {
    var [zapisanePredmety, zapisaneMessage] =
      cache.get("zapis_get_zapisane_predmety", query.zapisnyListKey, "SC") ||
      [];
    var [ponukanePredmety, ponukaneMessage] =
      cache.get(
        "zapis_ponuka_vyhladaj",
        query.zapisnyListKey,
        query.fakulta || null,
        query.stredisko || null,
        query.skratkaPredmetu || null,
        query.nazovPredmetu || null
      ) || [];
    akademickyRok = cache.get(
      "zapisny_list_key_to_akademicky_rok",
      query.zapisnyListKey
    );

    if (zapisaneMessage) {
      outerMessage = <p>{zapisaneMessage}</p>;
    } else if (!cache.loadedAll) {
      outerMessage = <Loading requests={cache.missing} />;
    } else {
      predmety = {};
      for (const predmet of ponukanePredmety) {
        predmety[predmet.predmet_key] = { moje: false, ...predmet };
      }
      for (const predmet of zapisanePredmety) {
        if (predmety[predmet.predmet_key]) {
          predmety[predmet.predmet_key].moje = true;
        }
      }

      tableMessage = ponukaneMessage;
      if (_.isEmpty(predmety) && !tableMessage) {
        tableMessage = "Podmienkam nevyhovuje žiadny záznam.";
      }
    }
  }

  return (
    <React.Fragment>
      <ZapisMenu />
      <ZapisZPonukyForm />
      {outerMessage}
      {predmety && <h2>Výsledky</h2>}
      <ZapisTable
        predmety={predmety}
        message={tableMessage}
        akademickyRok={akademickyRok}
        odoberPredmety={odoberPredmety}
        pridajPredmety={pridajPredmety}
        columns={ZapisZPonukyColumns}
      />
    </React.Fragment>
  );

  function pridajPredmety(predmety, callback) {
    if (!predmety.length) return callback(null);

    var skratky = predmety.map((predmet) => predmet.skratka);
    sendRpc(
      "zapis_ponuka_pridaj_predmety",
      [
        query.zapisnyListKey,
        query.fakulta || null,
        query.stredisko || null,
        query.skratkaPredmetu || null,
        query.nazovPredmetu || null,
        skratky,
      ],
      callback
    );
  }

  function odoberPredmety(predmety, callback) {
    if (!predmety.length) return callback(null);

    var kluce = predmety.map((predmet) => predmet.predmet_key);
    sendRpc(
      "zapis_odstran_predmety",
      [query.zapisnyListKey, "SC", kluce],
      callback
    );
  }
}

export function makeZapisZPonukyPage() {
  return (
    <PageLayout>
      <ZapisnyListSelector>
        <ZapisZPonukyPageContent />
      </ZapisnyListSelector>
    </PageLayout>
  );
}
