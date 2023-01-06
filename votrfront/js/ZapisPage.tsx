import classNames from "classnames";
import _ from "lodash";
import React, { useContext, useState } from "react";
import {
  CacheRequester,
  invalidateRequestCache,
  Loading,
  sendRpc,
} from "./ajax";
import { coursesStats } from "./coursesStats";
import { humanizeTypVyucby, plural } from "./humanizeAISData";
import { FormItem, PageLayout, PageTitle } from "./layout";
import { ScreenSize } from "./mediaQueries";
import { Link, navigate, QueryContext, RelativeLink } from "./router";
import { SortableTable, sortAs } from "./sorting";
import {
  Columns,
  ComboBoxOption,
  Href,
  ZapisCast,
  ZapisPredmet,
} from "./types";
import { ZapisnyListSelector } from "./ZapisnyListSelector";

const pocetPrihlasenychJeStaryStore = new Set<string>();

const typVyucbyColumn = {
  label: <abbr title="Typ výučby">Typ</abbr>,
  prop: "typ_vyucby",
  display: (predmet: ZapisPredmet) => (
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
  sortKey: sortAs.number,
  hiddenClass: ["hidden-xs"],
};
const prihlaseniColumn = {
  label: "Prihlásení",
  prop: "pocet_prihlasenych",
  sortKey: sortAs.number,
  display: (predmet: ZapisPredmet) => (
    <React.Fragment>
      {pocetPrihlasenychJeStaryStore.has(predmet.predmet_key) ? (
        <del>{predmet.pocet_prihlasenych}</del>
      ) : (
        predmet.pocet_prihlasenych
      )}
      {!!predmet.maximalne_prihlasenych && "/" + predmet.maximalne_prihlasenych}
    </React.Fragment>
  ),
  hiddenClass: ["hidden-xs"],
};
const jazykColumn = {
  label: "Jazyk",
  prop: "jazyk",
  display: (predmet: ZapisPredmet) => predmet.jazyk.replace(/ ,/g, ", "),
  hiddenClass: ["hidden-xs", "hidden-sm"],
};

var ZapisZPlanuColumns: Columns = [
  typVyucbyColumn,
  {
    label: "Blok",
    sortKey: (predmet: ZapisPredmet) =>
      parseInt(predmet.blok_index || "0") * 1000 +
      parseInt(predmet.v_bloku_index || "0"),
    hiddenClass: ["hidden-xs", "hidden-sm"],
    display: (predmet: ZapisPredmet) =>
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

var ZapisZPonukyColumns: Columns = [
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

var ZapisVlastnostiColumns = [
  { label: "Skratka", prop: "skratka", expansionMark: true },
  { label: "Názov", prop: "nazov" },
  { label: "Minimálny kredit", prop: "minimalny_kredit" },
  { label: "Poznámka", prop: "poznamka" },
];

function ZapisLink(props: { active: boolean; href: Href; label: string }) {
  return (
    <Link
      className={classNames("btn", "btn-default", props.active && "active")}
      href={props.href}
    >
      {props.label}
    </Link>
  );
}

function ZapisMenu() {
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

function ZapisTableFooter(props: {
  predmety: Map<string, ZapisPredmet>;
  moje: Record<string, boolean>;
  size: ScreenSize;
}) {
  const blokMoje = new Map<string, ZapisPredmet[]>();
  const vsetkyMoje: ZapisPredmet[] = [];
  const blokNazvy = new Map<string, string>();
  const semestre = new Set<string>();

  for (const predmet of props.predmety.values()) {
    const { predmet_key, semester, blok_skratka, blok_nazov } = predmet;
    semestre.add(semester);
    if (blok_skratka) {
      if (blok_nazov) blokNazvy.set(blok_skratka, blok_nazov);
      let list = blokMoje.get(blok_skratka);
      if (!list) blokMoje.set(blok_skratka, (list = []));
      if (props.moje[predmet_key]) list.push(predmet);
    }
    if (props.moje[predmet_key]) vsetkyMoje.push(predmet);
  }

  const zoradene = _.sortBy(Array.from(blokMoje.entries()), 0);
  zoradene.push(["", vsetkyMoje]);

  const jedinySemester = semestre.size <= 1;

  return (
    <React.Fragment>
      {zoradene.map(([skratka, mojePredmetyVBloku]) => {
        var stats = coursesStats(mojePredmetyVBloku as any);
        var nazov = blokNazvy.get(skratka);
        {
          return props.size > ScreenSize.SM ? (
            <tr key={skratka}>
              <td colSpan={2}>{skratka ? "Súčet bloku" : "Dokopy"}</td>
              <td>{nazov ? <abbr title={nazov}>{skratka}</abbr> : skratka}</td>
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
          ) : (
            <tr key={skratka}>
              <td>{skratka ? "Súčet bloku" : "Dokopy"}</td>
              <td>{nazov ? <abbr title={nazov}>{skratka}</abbr> : skratka}</td>
              <td colSpan={2}>
                {stats.spolu.count}{" "}
                {plural(stats.spolu.count, "predmet", "predmety", "predmetov")}
                {!jedinySemester &&
                  ` (${stats.zima.count} v zime, ${stats.leto.count} v lete)`}
                {props.size != ScreenSize.SM && (
                  <React.Fragment>
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
                  </React.Fragment>
                )}
              </td>
              {props.size == ScreenSize.SM && (
                <td colSpan={2}>
                  {stats.spolu.creditsEnrolled}
                  {!jedinySemester &&
                    ` (${stats.zima.creditsEnrolled}+${stats.leto.creditsEnrolled})`}
                </td>
              )}
            </tr>
          );
        }
      })}
    </React.Fragment>
  );
}

function ZapisTable(props: {
  predmety: Map<string, ZapisPredmet & { moje: boolean }> | undefined;
  odoberPredmety: (
    predmety: ZapisPredmet[],
    callback: (message: string | null) => void
  ) => void;
  pridajPredmety: (
    predmety: ZapisPredmet[],
    callback: (message: string | null) => void
  ) => void;
  akademickyRok: string | null | undefined;
  columns: Columns;
  showFooter?: boolean;
  message: string | null | undefined;
}) {
  var [saving, setSaving] = useState(false);
  var [changes, setChanges] = useState<Record<string, boolean | undefined>>({});

  const predmety = props.predmety;

  // Chceme, aby sa pre ZapisTable zachoval state aj vtedy, ked tabulku
  // nevidno, lebo sme prave zapisali predmety a obnovujeme zoznam predmetov.
  // Takze komponent ZapisTable sa bude renderovat vzdy, aby nikdy nezanikol
  // a neprisiel o state. Niekedy proste dostane predmety == undefined.
  if (!predmety || !props.akademickyRok) {
    return <span />;
  }

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    var predmetKey = event.target.name;
    var predmet = predmety.get(predmetKey)!;

    // prettier-ignore
    var want =
      predmet.moje && !event.target.checked ? false :
      !predmet.moje && event.target.checked ? true :
      undefined;
    setChanges((changes) => ({ ...changes, [predmetKey]: want }));
  };

  const handleSave = (event: React.FormEvent) => {
    event.preventDefault();

    if (saving) return;

    var odoberanePredmety: ZapisPredmet[] = [],
      pridavanePredmety: ZapisPredmet[] = [];
    for (const predmet of predmety.values()) {
      if (changes[predmet.predmet_key] === false && predmet.moje) {
        odoberanePredmety.push(predmet);
      }
      if (changes[predmet.predmet_key] === true && !predmet.moje) {
        pridavanePredmety.push(predmet);
      }
    }

    setSaving(true);

    var koniec = (odobral: boolean, pridal: boolean) => {
      setSaving(false);

      if (odobral) {
        for (const predmet of odoberanePredmety) {
          pocetPrihlasenychJeStaryStore.add(predmet.predmet_key);
        }
        setChanges((changes) => _.pickBy(changes, (value) => value === true));
      }

      if (pridal) {
        for (const predmet of pridavanePredmety) {
          pocetPrihlasenychJeStaryStore.add(predmet.predmet_key);
        }
        setChanges((changes) => _.pickBy(changes, (value) => value === false));
      }

      // Aj ked skoncime neuspechom, je mozne, ze niektore predmety sa zapisali.
      invalidateRequestCache("get_hodnotenia");
      invalidateRequestCache("get_predmety");
      invalidateRequestCache("get_prehlad_kreditov");
      invalidateRequestCache("get_studenti_zapisani_na_predmet");
      invalidateRequestCache("zapis_get_zapisane_predmety");
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
  };

  var classes: Record<string, string> = {},
    checked: Record<string, boolean> = {};
  for (const predmet of predmety.values()) {
    const predmet_key = predmet.predmet_key;
    checked[predmet.predmet_key] = predmet.moje;
    if (changes[predmet_key] === false && predmet.moje) {
      classes[predmet_key] = "danger";
      checked[predmet_key] = false;
    }
    if (changes[predmet_key] === true && !predmet.moje) {
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
    cellProps: () => ({ className: "text-center" }),
    display: (predmet: ZapisPredmet) => (
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
    display: (predmet: ZapisPredmet & { moje: boolean }) => {
      var href = {
        modal: "detailPredmetu",
        modalPredmetKey: predmet.predmet_key,
        modalAkademickyRok: props.akademickyRok,
      };
      var nazov = <RelativeLink href={href}>{predmet.nazov}</RelativeLink>;
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

  const footer = (size: ScreenSize) =>
    props.showFooter && (
      <ZapisTableFooter predmety={predmety} moje={checked} size={size} />
    );

  return (
    <form onSubmit={handleSave}>
      {saveButton}
      <SortableTable
        items={Array.from(predmety.values())}
        columns={columns}
        queryKey="predmetySort"
        footer={footer}
        message={props.message}
      />
      {saveButton}
    </form>
  );
}

function ZapisVlastnostiTable() {
  var query = useContext(QueryContext);
  var zapisnyListKey = query.zapisnyListKey!;
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

function ZapisZPlanuPageContent() {
  var query = useContext(QueryContext);
  var zapisnyListKey = query.zapisnyListKey!;
  var cast: ZapisCast = query.cast == "SS" ? "SS" : "SC";

  var cache = new CacheRequester();

  var [zapisanePredmety, zapisaneMessage] =
    cache.get("zapis_get_zapisane_predmety", zapisnyListKey, cast) || [];
  var [ponukanePredmety, ponukaneMessage] =
    cache.get("zapis_plan_vyhladaj", zapisnyListKey, cast) || [];
  var akademickyRok = cache.get(
    "zapisny_list_key_to_akademicky_rok",
    zapisnyListKey
  );

  var outerMessage,
    tableMessage,
    predmety: Map<string, ZapisPredmet & { moje: boolean }> | undefined;

  if (zapisaneMessage || ponukaneMessage) {
    outerMessage = <p>{zapisaneMessage || ponukaneMessage}</p>;
  } else if (!cache.loadedAll) {
    outerMessage = <Loading requests={cache.missing} />;
  } else {
    var vidnoZimne = false;

    predmety = new Map();
    for (const predmet of ponukanePredmety!) {
      predmety.set(predmet.predmet_key, { moje: false, ...predmet });
      if (predmet.semester == "Z") vidnoZimne = true;
    }
    for (const predmet of zapisanePredmety!) {
      var predmet_key = predmet.predmet_key;
      const existingPredmet = predmety.get(predmet_key);
      if (!existingPredmet) {
        if (predmet.semester == "Z" && !vidnoZimne) continue;
        predmety.set(predmet_key, { moje: true, ...predmet });
      } else {
        for (var property in predmet) {
          if (
            (predmet as any)[property] !== null &&
            (predmet as any)[property] !== undefined
          ) {
            (existingPredmet as any)[property] = (predmet as any)[property];
          }
        }
        existingPredmet.moje = true;
      }
    }

    if (predmety.size == 0) {
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

  function pridajPredmety(
    predmety: ZapisPredmet[],
    callback: (message: string | null) => void
  ) {
    if (!predmety.length) return callback(null);

    var dvojice: [string, string][] = predmety.map((predmet) => [
      predmet.typ_vyucby,
      predmet.skratka,
    ]);
    sendRpc(
      "zapis_plan_pridaj_predmety",
      [zapisnyListKey, cast, dvojice],
      callback
    );
  }

  function odoberPredmety(
    predmety: ZapisPredmet[],
    callback: (message: string | null) => void
  ) {
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

function ZapisZPonukyForm() {
  var query = useContext(QueryContext);
  var zapisnyListKey = query.zapisnyListKey!;

  var [state, setState] = useState({
    fakulta: query.fakulta,
    stredisko: query.stredisko,
    skratkaPredmetu: query.skratkaPredmetu,
    nazovPredmetu: query.nazovPredmetu,
  });

  function handleFieldChange(
    event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) {
    var name = event.target.name;
    var value = event.target.value;
    setState((old) => ({ ...old, [name]: value }));
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    navigate({ action: "zapisZPonuky", zapisnyListKey, ...state });
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
    items: ComboBoxOption[]
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

  var [fakulty, message] =
    cache.get("zapis_ponuka_options", zapisnyListKey) || [];

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

function ZapisZPonukyPageContent() {
  var query = useContext(QueryContext);
  var zapisnyListKey = query.zapisnyListKey!;
  var cache = new CacheRequester();

  var outerMessage,
    tableMessage,
    predmety: Map<string, ZapisPredmet & { moje: boolean }> | undefined,
    akademickyRok;

  if (
    query.fakulta ||
    query.stredisko ||
    query.skratkaPredmetu ||
    query.nazovPredmetu
  ) {
    var [zapisanePredmety, zapisaneMessage] =
      cache.get("zapis_get_zapisane_predmety", zapisnyListKey, "SC") || [];
    var [ponukanePredmety, ponukaneMessage] =
      cache.get(
        "zapis_ponuka_vyhladaj",
        zapisnyListKey,
        query.fakulta || null,
        query.stredisko || null,
        query.skratkaPredmetu || null,
        query.nazovPredmetu || null
      ) || [];
    akademickyRok = cache.get(
      "zapisny_list_key_to_akademicky_rok",
      zapisnyListKey
    );

    if (zapisaneMessage) {
      outerMessage = <p>{zapisaneMessage}</p>;
    } else if (!cache.loadedAll) {
      outerMessage = <Loading requests={cache.missing} />;
    } else {
      predmety = new Map();
      for (const predmet of ponukanePredmety!) {
        predmety.set(predmet.predmet_key, { moje: false, ...predmet });
      }
      for (const predmet of zapisanePredmety!) {
        const existingPredmet = predmety.get(predmet.predmet_key);
        if (existingPredmet) existingPredmet.moje = true;
      }

      tableMessage = ponukaneMessage;
      if (predmety.size == 0 && !tableMessage) {
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

  function pridajPredmety(
    predmety: ZapisPredmet[],
    callback: (message: string | null) => void
  ) {
    if (!predmety.length) return callback(null);

    var skratky = predmety.map((predmet) => predmet.skratka);
    sendRpc(
      "zapis_ponuka_pridaj_predmety",
      [
        zapisnyListKey,
        query.fakulta || null,
        query.stredisko || null,
        query.skratkaPredmetu || null,
        query.nazovPredmetu || null,
        skratky,
      ],
      callback
    );
  }

  function odoberPredmety(
    predmety: ZapisPredmet[],
    callback: (message: string | null) => void
  ) {
    if (!predmety.length) return callback(null);

    var kluce = predmety.map((predmet) => predmet.predmet_key);
    sendRpc("zapis_odstran_predmety", [zapisnyListKey, "SC", kluce], callback);
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

Votr.dev_pocetPrihlasenychJeStaryStore = pocetPrihlasenychJeStaryStore;
