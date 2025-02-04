import classNames from "classnames";
import { isEmpty, pickBy, sortBy } from "lodash-es";
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
import { ScreenSize, underSM, underXS } from "./mediaQueries";
import { Link, navigate, QueryContext, RelativeLink } from "./router";
import { type Column, column, SortableTable, sortAs } from "./sorting";
import type {
  ComboBoxOption,
  Href,
  ZapisCast,
  ZapisPredmet,
  ZapisVlastnost,
} from "./types";
import { ZapisnyListSelector } from "./ZapisnyListSelector";

const pocetPrihlasenychJeStaryStore = new Set<string>();

interface MojZapisPredmet extends ZapisPredmet {
  // server neposiela `moje`, vyrabame ho na klientovi kombinaciou dvoch RPC:
  // (zapis_plan_vyhladaj|zapis_ponuka_vyhladaj) + zapis_get_zapisane_predmety.
  moje: boolean;
}

const zapisVlastnostiColumns: Column<ZapisVlastnost>[] = [
  column({ label: "Skratka", prop: "skratka", expansionMark: true }),
  column({ label: "Názov", prop: "nazov" }),
  column({ label: "Minimálny kredit", prop: "minimalny_kredit" }),
  column({ label: "Poznámka", prop: "poznamka" }),
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
  const { action, cast, zapisnyListKey } = useContext(QueryContext);
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

  const zoradene = sortBy(Array.from(blokMoje.entries()), 0);
  zoradene.push(["", vsetkyMoje]);

  const jedinySemester = semestre.size <= 1;

  return (
    <React.Fragment>
      {zoradene.map(([skratka, mojePredmetyVBloku]) => {
        const stats = coursesStats(mojePredmetyVBloku);
        const nazov = blokNazvy.get(skratka);
        const blok = nazov ? <abbr title={nazov}>{skratka}</abbr> : skratka;
        const uvod = skratka ? "Súčet bloku" : "Dokopy";
        const uvodABlok =
          skratka ? <React.Fragment>Σ {blok}</React.Fragment> : "Dokopy";
        const pocet =
          `${stats.spolu.count} ` +
          plural(stats.spolu.count, "predmet", "predmety", "predmetov") +
          (jedinySemester ? "" : (
            ` (${stats.zima.count} v zime, ${stats.leto.count} v lete)`
          ));
        const kredity =
          String(stats.spolu.creditsEnrolled) +
          (jedinySemester ? "" : (
            ` (${stats.zima.creditsEnrolled}+${stats.leto.creditsEnrolled})`
          ));
        const pocetAKredity = `${pocet}, ${kredity} kreditov`;
        return (
          props.size == ScreenSize.XS ?
            <tr key={skratka}>
              <td colSpan={2}>{uvodABlok}</td>
              <td colSpan={2}>{pocetAKredity}</td>
            </tr>
          : props.size == ScreenSize.SM ?
            <tr key={skratka}>
              <td colSpan={2}>{uvodABlok}</td>
              <td colSpan={2}>{pocet}</td>
              <td colSpan={2}>{kredity}</td>
            </tr>
          : <tr key={skratka}>
              <td colSpan={2}>{uvod}</td>
              <td>{blok}</td>
              <td colSpan={4}>{pocet}</td>
              <td>{kredity}</td>
              <td></td>
              <td></td>
              <td></td>
            </tr>
        );
      })}
    </React.Fragment>
  );
}

function ZapisTable({
  predmety,
  odoberPredmety,
  pridajPredmety,
  akademickyRok,
  zPlanu,
  tableMessage,
}: {
  predmety: Map<string, MojZapisPredmet> | undefined;
  odoberPredmety: (
    predmety: ZapisPredmet[],
    callback: (mutationMessage: string | null) => void,
  ) => void;
  pridajPredmety: (
    predmety: ZapisPredmet[],
    callback: (mutationMessage: string | null) => void,
  ) => void;
  akademickyRok: string | undefined;
  zPlanu: boolean;
  tableMessage: string | null | undefined;
}) {
  const [saving, setSaving] = useState(false);
  const [changes, setChanges] = useState<Record<string, boolean | undefined>>(
    {},
  );

  // Chceme, aby sa pre ZapisTable zachoval state aj vtedy, ked tabulku
  // nevidno, lebo sme prave zapisali predmety a obnovujeme zoznam predmetov.
  // Takze komponent ZapisTable sa bude renderovat vzdy, aby nikdy nezanikol
  // a neprisiel o state. Niekedy proste dostane predmety == undefined.
  if (!predmety || !akademickyRok) {
    return <span />;
  }

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const predmetKey = event.target.name;
    const predmet = predmety.get(predmetKey)!;

    const want =
      predmet.moje && !event.target.checked ? false
      : !predmet.moje && event.target.checked ? true
      : undefined;
    setChanges((changes) => ({ ...changes, [predmetKey]: want }));
  };

  const handleSave = (event: React.FormEvent) => {
    event.preventDefault();

    if (saving) return;

    const odoberanePredmety: ZapisPredmet[] = [],
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

    const koniec = (odobral: boolean, pridal: boolean) => {
      setSaving(false);

      if (odobral) {
        for (const predmet of odoberanePredmety) {
          pocetPrihlasenychJeStaryStore.add(predmet.predmet_key);
        }
        setChanges((changes) => pickBy(changes, (value) => value === true));
      }

      if (pridal) {
        for (const predmet of pridavanePredmety) {
          pocetPrihlasenychJeStaryStore.add(predmet.predmet_key);
        }
        setChanges((changes) => pickBy(changes, (value) => value === false));
      }

      // Aj ked skoncime neuspechom, je mozne, ze niektore predmety sa zapisali.
      invalidateRequestCache("get_hodnotenia");
      invalidateRequestCache("get_predmety");
      invalidateRequestCache("get_prehlad_kreditov");
      invalidateRequestCache("get_studenti_zapisani_na_predmet");
      invalidateRequestCache("zapis_get_zapisane_predmety");
    };

    odoberPredmety(odoberanePredmety, (mutationMessage) => {
      if (mutationMessage) {
        alert(mutationMessage);
        koniec(false, false);
      } else {
        pridajPredmety(pridavanePredmety, (mutationMessage) => {
          if (mutationMessage) {
            alert(mutationMessage);
            koniec(true, false);
          } else {
            koniec(true, true);
          }
        });
      }
    });
  };

  const classes: Record<string, string> = {},
    checked: Record<string, boolean> = {};
  for (const predmet of predmety.values()) {
    const predmetKey = predmet.predmet_key;
    checked[predmetKey] = predmet.moje;
    if (changes[predmetKey] === false && predmet.moje) {
      classes[predmetKey] = "danger";
      checked[predmetKey] = false;
    }
    if (changes[predmetKey] === true && !predmet.moje) {
      classes[predmetKey] = "success";
      checked[predmetKey] = true;
    }
  }

  const saveButton = (
    <div className="section">
      <button
        type="submit"
        className="btn btn-primary"
        disabled={isEmpty(classes)}
      >
        {saving ?
          <Loading />
        : "Uložiť zmeny"}
      </button>
    </div>
  );

  const columns: Column<MojZapisPredmet>[] = [
    // #0
    column({
      label: "Moje?",
      sortKey: (predmet: MojZapisPredmet) => predmet.moje,
      preferDesc: true,
      cellProps: () => ({ className: "text-center" }),
      display: (predmet: MojZapisPredmet) => (
        <input
          type="checkbox"
          name={predmet.predmet_key}
          checked={checked[predmet.predmet_key]}
          onChange={handleChange}
        />
      ),
    }),

    // #1
    column({
      label: <abbr title="Typ výučby">Typ</abbr>,
      prop: "typ_vyucby",
      display: (value: string) => (
        <abbr title={humanizeTypVyucby(value)}>{value}</abbr>
      ),
    }),

    // #2
    zPlanu ?
      column({
        label: "Blok",
        sortKey: (predmet: ZapisPredmet) =>
          parseInt(predmet.blok_index || "0") * 1000 +
          parseInt(predmet.v_bloku_index || "0"),
        hide: underSM,
        display: (predmet: ZapisPredmet) =>
          predmet.blok_nazov ?
            <abbr title={predmet.blok_nazov}>{predmet.blok_skratka}</abbr>
          : predmet.blok_skratka,
      })
    : column({ label: "Blok", prop: "blok_skratka", hide: underSM }),

    // #3
    column({
      label: "Názov predmetu",
      sortKey: (predmet: MojZapisPredmet) => predmet.nazov,
      expansionMark: true,
      display: (predmet: MojZapisPredmet) => {
        const href = {
          modal: "detailPredmetu",
          modalPredmetKey: predmet.predmet_key,
          modalAkademickyRok: akademickyRok,
        };
        let nazov = <RelativeLink href={href}>{predmet.nazov}</RelativeLink>;
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
    }),

    // #4
    column({ label: "Skratka predmetu", prop: "skratka", hide: underSM }),

    // #5
    column({
      label: "Semester",
      shortLabel: <abbr title="Semester">Sem.</abbr>,
      prop: "semester",
      preferDesc: true,
    }),

    // #6
    column({ label: "Rozsah výučby", prop: "rozsah_vyucby", hide: underSM }),

    // #7
    column({
      label: "Kredit",
      prop: "kredit",
      sortKey: sortAs.number,
      hide: underXS,
    }),

    // #8
    column({
      label: "Prihlásení",
      sortKey: (predmet: ZapisPredmet) =>
        sortAs.number(predmet.pocet_prihlasenych || "0"),
      display: (predmet: ZapisPredmet) => (
        <React.Fragment>
          {pocetPrihlasenychJeStaryStore.has(predmet.predmet_key) ?
            <del>{predmet.pocet_prihlasenych}</del>
          : predmet.pocet_prihlasenych}
          {!!predmet.maximalne_prihlasenych &&
            "/" + predmet.maximalne_prihlasenych}
        </React.Fragment>
      ),
      hide: underXS,
    }),

    // #9?
    ...(zPlanu ?
      [
        column({
          label: "Odporúčaný ročník",
          shortLabel: <abbr title="Odporúčaný ročník">Odp. ročník</abbr>,
          prop: "odporucany_rocnik",
          hide: underSM,
        }),
      ]
    : []),

    // #9 / #10
    column({
      label: "Jazyk",
      projection: (predmet: ZapisPredmet) => predmet.jazyk.replace(/ ,/g, ", "),
      hide: underSM,
    }),
  ];

  // Z planu: Typ, Blok, Odporucany rocnik, Nazov. Z ponuky: Nazov.
  const defaultOrder = zPlanu ? "a1a2a9a3" : "a3";

  const footer = (size: ScreenSize) =>
    zPlanu && (
      <ZapisTableFooter predmety={predmety} moje={checked} size={size} />
    );

  return (
    <form onSubmit={handleSave}>
      {saveButton}
      <SortableTable
        items={Array.from(predmety.values())}
        columns={columns}
        defaultOrder={defaultOrder}
        queryKey="predmetySort"
        footer={footer}
        message={tableMessage}
      />
      {saveButton}
    </form>
  );
}

function ZapisVlastnostiTable() {
  const query = useContext(QueryContext);
  const zapisnyListKey = query.zapisnyListKey!;
  const cache = new CacheRequester();

  const [vlastnosti, serverMessage] =
    cache.get("zapis_get_vlastnosti_programu", zapisnyListKey) || [];

  if (!vlastnosti) {
    return <Loading requests={cache.missing} />;
  }

  const message =
    serverMessage ||
    (vlastnosti.length ? null : "Študijný plán nemá žiadne poznámky.");

  return (
    <SortableTable
      items={vlastnosti}
      columns={zapisVlastnostiColumns}
      queryKey="vlastnostiSort"
      message={message}
    />
  );
}

function ZapisZPlanuPageContent() {
  const query = useContext(QueryContext);
  const zapisnyListKey = query.zapisnyListKey!;
  const cast: ZapisCast = query.cast == "SS" ? "SS" : "SC";

  const cache = new CacheRequester();

  const [zapisanePredmety, zapisaneMessage] =
    cache.get("zapis_get_zapisane_predmety", zapisnyListKey, cast) || [];
  const [ponukanePredmety, ponukaneMessage] =
    cache.get("zapis_plan_vyhladaj", zapisnyListKey, cast) || [];
  const akademickyRok = cache.get(
    "zapisny_list_key_to_akademicky_rok",
    zapisnyListKey,
  );

  let outerMessage,
    tableMessage,
    predmety: Map<string, MojZapisPredmet> | undefined;

  if (zapisaneMessage || ponukaneMessage) {
    outerMessage = <p>{zapisaneMessage || ponukaneMessage}</p>;
  } else if (!cache.loadedAll) {
    outerMessage = <Loading requests={cache.missing} />;
  } else {
    let vidnoZimne = false;

    predmety = new Map();
    for (const predmet of ponukanePredmety!) {
      predmety.set(predmet.predmet_key, { moje: false, ...predmet });
      if (predmet.semester == "Z") vidnoZimne = true;
    }
    for (const predmet of zapisanePredmety!) {
      const predmetKey = predmet.predmet_key;
      const existingPredmet = predmety.get(predmetKey);
      if (!existingPredmet) {
        if (predmet.semester == "Z" && !vidnoZimne) continue;
        predmety.set(predmetKey, { moje: true, ...predmet });
      } else {
        for (const property in predmet) {
          if (
            (predmet as any)[property] !== null && // eslint-disable-line
            (predmet as any)[property] !== undefined // eslint-disable-line
          ) {
            (existingPredmet as any)[property] = (predmet as any)[property]; // eslint-disable-line
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
        tableMessage={tableMessage}
        akademickyRok={akademickyRok}
        odoberPredmety={odoberPredmety}
        pridajPredmety={pridajPredmety}
        zPlanu={true}
      />
      <h2>Poznámky k študijnému plánu</h2>
      <ZapisVlastnostiTable />
    </React.Fragment>
  );

  function pridajPredmety(
    predmety: ZapisPredmet[],
    callback: (mutationMessage: string | null) => void,
  ) {
    if (!predmety.length) {
      callback(null);
      return;
    }

    const dvojice: [string, string][] = predmety.map((predmet) => [
      predmet.typ_vyucby,
      predmet.skratka,
    ]);
    sendRpc(
      "zapis_plan_pridaj_predmety",
      [zapisnyListKey, cast, dvojice],
      callback,
    );
  }

  function odoberPredmety(
    predmety: ZapisPredmet[],
    callback: (mutationMessage: string | null) => void,
  ) {
    if (!predmety.length) {
      callback(null);
      return;
    }

    const kluce = predmety.map((predmet) => predmet.predmet_key);
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
  const query = useContext(QueryContext);
  const zapisnyListKey = query.zapisnyListKey!;

  const [state, setState] = useState({
    fakulta: query.fakulta,
    stredisko: query.stredisko,
    skratkaPredmetu: query.skratkaPredmetu,
    nazovPredmetu: query.nazovPredmetu,
  });

  function handleFieldChange(
    event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) {
    const name = event.target.name;
    const value = event.target.value;
    setState((old) => ({ ...old, [name]: value }));
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    navigate({ action: "zapisZPonuky", zapisnyListKey, ...state });
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
    items: ComboBoxOption[],
  ) {
    return (
      <FormItem label={label}>
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
      </FormItem>
    );
  }

  const [fakulty, message] =
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
  const query = useContext(QueryContext);
  const zapisnyListKey = query.zapisnyListKey!;
  const cache = new CacheRequester();

  let outerMessage,
    tableMessage,
    predmety: Map<string, MojZapisPredmet> | undefined,
    akademickyRok;

  if (
    query.fakulta ||
    query.stredisko ||
    query.skratkaPredmetu ||
    query.nazovPredmetu
  ) {
    const [zapisanePredmety, zapisaneMessage] =
      cache.get("zapis_get_zapisane_predmety", zapisnyListKey, "SC") || [];
    const [ponukanePredmety, ponukaneMessage] =
      cache.get(
        "zapis_ponuka_vyhladaj",
        zapisnyListKey,
        query.fakulta || null,
        query.stredisko || null,
        query.skratkaPredmetu || null,
        query.nazovPredmetu || null,
      ) || [];
    akademickyRok = cache.get(
      "zapisny_list_key_to_akademicky_rok",
      zapisnyListKey,
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
        tableMessage={tableMessage}
        akademickyRok={akademickyRok}
        odoberPredmety={odoberPredmety}
        pridajPredmety={pridajPredmety}
        zPlanu={false}
      />
    </React.Fragment>
  );

  function pridajPredmety(
    predmety: ZapisPredmet[],
    callback: (mutationMessage: string | null) => void,
  ) {
    if (!predmety.length) {
      callback(null);
      return;
    }

    const skratky = predmety.map((predmet) => predmet.skratka);
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
      callback,
    );
  }

  function odoberPredmety(
    predmety: ZapisPredmet[],
    callback: (mutationMessage: string | null) => void,
  ) {
    if (!predmety.length) {
      callback(null);
      return;
    }

    const kluce = predmety.map((predmet) => predmet.predmet_key);
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
