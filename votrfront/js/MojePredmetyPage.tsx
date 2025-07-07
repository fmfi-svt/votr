import { escape } from "lodash-es";
import React, { useContext } from "react";
import { CacheRequester, Loading } from "./ajax";
import { coursesStats, neuspesneZnamky } from "./coursesStats";
import {
  classForSemester,
  humanizeTerminHodnotenia,
  humanizeTypVyucby,
  plural,
} from "./humanizeAISData";
import { InfoTooltip, PageLayout, PageTitle } from "./layout";
import { ScreenSize, underSM, underXS } from "./mediaQueries";
import { QueryContext, RelativeLink } from "./router";
import { type Column, column, SortableTable, sortAs } from "./sorting";
import type { Hodnotenie } from "./types";
import { ZapisnyListSelector } from "./ZapisnyListSelector";

export const mojePredmetyColumns: Column<Hodnotenie>[] = [
  column({
    label: "Semester",
    shortLabel: <abbr title="Semester">Sem.</abbr>,
    prop: "semester",
    preferDesc: true,
  }),
  column({
    label: "Názov predmetu",
    sortKey: (hodnotenie: Hodnotenie) => hodnotenie.nazov,
    display: (hodnotenie: Hodnotenie) => (
      <RelativeLink
        href={{
          modal: "detailPredmetu",
          modalPredmetKey: hodnotenie.predmet_key,
          modalAkademickyRok: hodnotenie.akademicky_rok,
        }}
      >
        {hodnotenie.nazov}
      </RelativeLink>
    ),
    expansionMark: true,
  }),
  column({ label: "Skratka predmetu", prop: "skratka", hide: underSM }),
  column({
    label: "Kredit",
    sortKey: (hodnotenie: Hodnotenie) => sortAs.number(hodnotenie.kredit),
    display: (hodnotenie: Hodnotenie) => {
      const neuspesny = neuspesneZnamky.has(hodnotenie.hodn_znamka);
      const nahradeny = hodnotenie.nahradeny;
      const nepotvrdeny = hodnotenie.poplatok != "A";
      if (neuspesny || nahradeny || nepotvrdeny) {
        const lines = [
          "Na výpočet kreditov a/alebo vážených priemerov môže vplývať:",
          neuspesny ? `Predmet má hodnotenie "${hodnotenie.hodn_znamka}".` : "",
          nahradeny ? "Predmet bol nahradený iným predmetom." : "",
          nepotvrdeny ?
            hodnotenie.poplatok == "" ?
              'Stĺpec "Potvrdený" ("Zaplatený poplatok a úplný zápis") je v AISe prázdny.'
            : `V stĺpci "Potvrdený" ("Zaplatený poplatok a úplný zápis") sa v AISe píše "${hodnotenie.poplatok}".`
          : "",
        ];
        return (
          <InfoTooltip
            content={<em>{hodnotenie.kredit}</em>}
            icon={"\u2139\uFE0F"}
            tooltipHtml={lines.filter(Boolean).map(escape).join("<br>")}
          />
        );
      } else {
        return hodnotenie.kredit;
      }
    },
  }),
  column({
    label: "Typ výučby",
    prop: "typ_vyucby",
    display: humanizeTypVyucby,
    hide: underXS,
  }),
  column({
    label: "Hodnotenie",
    projection: (hodnotenie: Hodnotenie) =>
      [hodnotenie.hodn_znamka, hodnotenie.hodn_znamka_popis]
        .filter(Boolean)
        .join(" - "),
  }),
  column({
    label: "Dátum hodnotenia",
    prop: "hodn_datum",
    sortKey: sortAs.date,
    hide: underSM,
  }),
  column({
    label: "Termín hodnotenia",
    prop: "hodn_termin",
    display: humanizeTerminHodnotenia,
    hide: underSM,
  }),
];

// Semester (descending), Nazov predmetu
const mojePredmetyDefaultOrder = "d0a1";

function MojePredmetyPageContent() {
  const query = useContext(QueryContext);
  const cache = new CacheRequester();
  const zapisnyListKey = query.zapisnyListKey!;

  const [hodnotenia, message] =
    cache.get("get_hodnotenia", zapisnyListKey) || [];

  if (!hodnotenia) {
    return <Loading requests={cache.missing} />;
  }

  const stats = coursesStats(hodnotenia);

  const footer = (size: ScreenSize) => (
    <tr>
      {size > ScreenSize.SM && <td />}
      <td colSpan={2}>
        <InfoTooltip
          content={
            <React.Fragment>
              Celkom {stats.spolu.count}{" "}
              {plural(stats.spolu.count, "predmet", "predmety", "predmetov")}
              {" ("}
              {stats.zima.count} v zime, {stats.leto.count} v lete)
            </React.Fragment>
          }
          icon={"\u2754"}
          tooltipHtml="Tieto čísla vypočítal Votr.<br>Nie sú oficiálne z AISu."
        />
      </td>
      <td>
        <InfoTooltip
          content={<em>{stats.spolu.creditsEnrolled}?</em>}
          icon={"\u2754"}
          tooltipHtml={
            "Toto číslo vypočítal Votr.<br>Nie je oficiálne z AISu.<br>" +
            `Celkom <strong>${stats.spolu.creditsEnrolled}</strong> kreditov ` +
            `(<strong>${stats.zima.creditsEnrolled}</strong> v zime, <strong>${stats.leto.creditsEnrolled}</strong> v lete).<br>` +
            "Do tohto súčtu sa počítajú <strong>všetky zapísané predmety</strong> &ndash; aj neúspešné, bez hodnotenia, alebo nahradené."
          }
        />
      </td>
      {size > ScreenSize.XS && <td />}
      <td />
      {size > ScreenSize.SM && <td />}
      {size > ScreenSize.SM && <td />}
    </tr>
  );

  return (
    <SortableTable
      items={hodnotenia}
      columns={mojePredmetyColumns}
      defaultOrder={mojePredmetyDefaultOrder}
      queryKey="predmetySort"
      expandedContentOffset={1}
      message={message}
      footer={footer}
      rowClassName={(hodnotenie) => classForSemester(hodnotenie.semester)}
    />
  );
}

export function makeMojePredmetyPage() {
  return (
    <PageLayout>
      <ZapisnyListSelector>
        <div className="v-common-header">
          <PageTitle>Moje predmety</PageTitle>
        </div>
        <MojePredmetyPageContent />
      </ZapisnyListSelector>
    </PageLayout>
  );
}
