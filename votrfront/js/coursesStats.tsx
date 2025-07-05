import { getDateNow } from "./now";
import type { Hodnotenie, ZapisPredmet } from "./types";

export function coursesStats(predmety: (Hodnotenie | ZapisPredmet)[]) {
  const result = {
    zima: { count: 0, creditsEnrolled: 0 },
    leto: { count: 0, creditsEnrolled: 0 },
    spolu: { count: 0, creditsEnrolled: 0 },
  };

  function add(type: "zima" | "leto" | "spolu", credits: number) {
    result[type].count++;
    result[type].creditsEnrolled += credits;
  }

  for (const row of predmety) {
    const credits = parseInt(row.kredit);
    add("spolu", credits);
    if (row.semester == "Z") add("zima", credits);
    if (row.semester == "L") add("leto", credits);
  }

  return result;
}

export function currentAcademicYear() {
  const date = getDateNow();

  const year = date.getFullYear();
  const month = date.getMonth() + 1;

  if (month < 8) {
    return `${year - 1}/${year}`;
  } else {
    return `${year}/${year + 1}`;
  }
}

export const neuspesneZnamky = new Set(["FX", "X", "NEABS", "N"]);
