import { useContext } from "react";
import { CacheRequester, Loading } from "./ajax";
import {
  coursesStats,
  renderCredits,
  renderWeightedStudyAverage,
} from "./coursesStats";
import { classForSemester, plural } from "./humanizeAISData";
import { PageLayout, PageTitle } from "./layout";
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

  const [hodnotenia, message] =
    cache.get("get_prehlad_kreditov", studiumKey) || [];

  if (!hodnotenia) {
    return <Loading requests={cache.missing} />;
  }

  const stats = coursesStats(hodnotenia);

  const footer = (size: ScreenSize) => (
    <tr>
      {size > ScreenSize.SM && <td colSpan={2} />}
      <td colSpan={2}>
        Celkom {stats.spolu.count}{" "}
        {plural(stats.spolu.count, "predmet", "predmety", "predmetov")}
      </td>
      <td>{renderCredits(stats.spolu)}</td>
      {size > ScreenSize.XS && <td />}
      <td>{renderWeightedStudyAverage(hodnotenia)}</td>
      {size > ScreenSize.SM && <td />}
      {size > ScreenSize.SM && <td />}
    </tr>
  );

  return (
    <SortableTable
      items={hodnotenia}
      columns={mojeHodnoteniaColumns}
      defaultOrder={mojeHodnoteniaDefaultOrder}
      queryKey="predmetySort"
      message={message}
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
