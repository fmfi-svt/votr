import { escape, max } from "lodash-es";
import React, { useContext } from "react";
import { CacheRequester, Loading } from "./ajax";
import { coursesStats, neuspesneZnamky } from "./coursesStats";
import { classForSemester, plural } from "./humanizeAISData";
import { InfoTooltip, PageLayout, PageTitle } from "./layout";
import { ScreenSize, underSM } from "./mediaQueries";
import { mojePredmetyColumns } from "./MojePredmetyPage";
import { QueryContext } from "./router";
import { type Column, column, SortableTable } from "./sorting";
import { StudiumSelector } from "./StudiumSelector";
import type { Hodnotenie } from "./types";

const [predmetSemesterColumn, ...predmetRemainingColumns] = mojePredmetyColumns;
const mojeHodnoteniaColumns: Column<Hodnotenie>[] = [
  column({ label: "Akademický rok", prop: "akademicky_rok" }),
  { ...predmetSemesterColumn!, hide: underSM },
  ...predmetRemainingColumns,
];

// Akademicky rok, Semester (descending), Nazov predmetu
const mojeHodnoteniaDefaultOrder = "a0d1a2";

function MojeHodnoteniaHodnoteniaTable() {
  const query = useContext(QueryContext);
  const cache = new CacheRequester();
  const studiumKey = query.studiumKey!;

  let result = cache.get("get_prehlad_kreditov", studiumKey);

  if (!result) {
    return <Loading requests={cache.missing} />;
  }

  // Legacy return type support (for flashbacks).
  if (Array.isArray(result)) {
    const [items, message] = result as unknown as [Hodnotenie[], string | null];
    result = {
      items,
      message,
      kredity_ziskane: null,
      kredity_zapisane: null,
      priemer_ohodnotenych: null,
      priemer_vsetkych: null,
    };
  }

  const stats = coursesStats(result.items);

  // Mame styri sucty kreditov, ktore mozu byt vsetky navzajom rozne:
  // A) kolko ukazuje AIS ako sucet ziskanych kreditov
  // B) kolko este stale mozes ziskat, ak zvladnes vsetky skusky
  // C) kolko ukazuje AIS ako sucet zapisanych kreditov
  // D) kolko mas fakt zapisanych kreditov (naivny sucet vsetkych riadkov)
  //
  // Podla vsetkeho co som videl, vyzera ze AIS pocita svoje sucty takto:
  // A) = sucet tych co nie su nahradene a maju znamku != "",FX,X,N,NEABS
  // C) = sucet tych co nie su nahradene
  //
  // Votr ukazuje iba oficialne cisla, A) a C), lebo kto vie ci su v pravidlach
  // dalsie vynimky o ktorych neviem. Ale osobne mi pride B) uzitocnejsie a
  // intuitivnejsie ako C). Preto by sme chceli varovat ludi co maju B) != C),
  // aby si nemysleli ze mozu ziskat viac ako naozaj mozu. Je to len best-effort
  // odhad, nevadi ak nasa znalost AIS pravidiel nie je celkom presna.
  const poslednyRok = max(result.items.map((h) => h.akademicky_rok));
  const varovanie =
    // Ak vsetky predmety maju znamku, uz je to jedno, nema zmysel varovat.
    result.items.some((hodnotenie) => !hodnotenie.hodn_znamka) &&
    // Existuje predmet co sa nepocita do B) ale pocita sa do C)?
    // Cize je *neuspesny* (uz zanho nejde ziskat kredity) ale nie *nahradeny*.
    // Predmety bez znamky su nejasne. Tipujeme podla toho ci su tohtorocne.
    result.items.some((hodnotenie) => {
      const predmetJeMoznoNeuspesny =
        neuspesneZnamky.has(hodnotenie.hodn_znamka) ||
        (hodnotenie.hodn_znamka == "" &&
          hodnotenie.akademicky_rok != poslednyRok);
      return predmetJeMoznoNeuspesny && !hodnotenie.nahradeny;
    });

  const footer = (size: ScreenSize) => (
    <tr>
      {size > ScreenSize.SM && <td colSpan={2} />}
      <td colSpan={2}>
        <InfoTooltip
          content={
            <React.Fragment>
              Celkom {stats.spolu.count}{" "}
              {plural(stats.spolu.count, "predmet", "predmety", "predmetov")}
            </React.Fragment>
          }
          icon={"\u2754"}
          tooltipHtml="Toto číslo vypočítal Votr.<br>Nie je oficiálne z AISu."
        />
      </td>
      <td>
        {result.kredity_ziskane != null && result.kredity_zapisane != null && (
          <InfoTooltip
            content={
              <span className={varovanie ? "text-danger" : ""}>
                {result.kredity_ziskane}/<wbr />
                {result.kredity_zapisane}
              </span>
            }
            icon={varovanie ? "\u26A0\uFE0F" : "\u2139\uFE0F"}
            tooltipHtml={
              `Súčet kreditov podľa AISu:<br>` +
              `Získané: <strong>${result.kredity_ziskane}</strong><br>` +
              `Zapísané: <strong>${result.kredity_zapisane}</strong>` +
              (varovanie ?
                "<br>Pozor: Do súčtu zapísaných kreditov sa môžu počítať aj niektoré neúspešné predmety! " +
                "Nemusí sa nutne zhodovať s počtom kreditov, ktoré môžete ešte stále získať, ak absolvujete zvyšné zapísané predmety."
              : "")
            }
          />
        )}
      </td>
      {size > ScreenSize.XS && <td />}
      <td>
        {result.priemer_ohodnotenych && (
          <InfoTooltip
            content={result.priemer_ohodnotenych}
            icon={"\u2139\uFE0F"}
            tooltipHtml={
              `Vážený študijný priemer podľa AISu (vrátane štátnych skúšok):<br>` +
              `Len ohodnotených predmetov: <strong>${escape(result.priemer_ohodnotenych)}</strong><br>` +
              `Všetkých predmetov: <strong>${escape(result.priemer_vsetkych || "?")}</strong><br>` +
              `Ďalšie typy priemerov nájdete v AISe.`
            }
          />
        )}
      </td>
      {size > ScreenSize.SM && <td />}
      {size > ScreenSize.SM && <td />}
    </tr>
  );

  return (
    <SortableTable
      items={result.items}
      columns={mojeHodnoteniaColumns}
      defaultOrder={mojeHodnoteniaDefaultOrder}
      queryKey="predmetySort"
      message={result.message}
      footer={footer}
      rowClassName={(hodnotenie) => classForSemester(hodnotenie.semester)}
    />
  );
}

export function makeMojeHodnoteniaPage() {
  return (
    <PageLayout>
      <StudiumSelector>
        <div className="v-common-header">
          <PageTitle>Moje hodnotenia</PageTitle>
        </div>
        <MojeHodnoteniaHodnoteniaTable />
      </StudiumSelector>
    </PageLayout>
  );
}
