import React from "react";
import { getDateNow } from "./now";
import { Hodnotenie, ZapisPredmet } from "./types";

const ZNAMKY: Record<string, number> = {
  "A": 1,
  "B": 1.5,
  "C": 2,
  "D": 2.5,
  "E": 3,
  "F": 4,
};

export function coursesStats(predmety: (Hodnotenie | ZapisPredmet)[]) {
  const result = {
    zima: { count: 0, creditsEnrolled: 0, creditsObtained: 0 },
    leto: { count: 0, creditsEnrolled: 0, creditsObtained: 0 },
    spolu: { count: 0, creditsEnrolled: 0, creditsObtained: 0 },
  };

  function add(
    type: "zima" | "leto" | "spolu",
    credits: number,
    obtained: boolean
  ) {
    result[type].count++;
    result[type].creditsEnrolled += credits;
    result[type].creditsObtained += obtained ? credits : 0;
  }

  for (const row of predmety) {
    const credits = parseInt(row.kredit);
    const obtained =
      "hodn_znamka" in row &&
      !!row.hodn_znamka &&
      !row.hodn_znamka.startsWith("F");
    add("spolu", credits, obtained);
    if (row.semester == "Z") add("zima", credits, obtained);
    if (row.semester == "L") add("leto", credits, obtained);
  }

  return result;
}

export function weightedStudyAverage(hodnotenia: Hodnotenie[]) {
  let weightedSum = 0;
  let creditsSum = 0;

  for (const row of hodnotenia) {
    const value = ZNAMKY[row.hodn_znamka.charAt(0)];
    if (value) {
      weightedSum += value * parseInt(row.kredit);
      creditsSum += parseInt(row.kredit);
    }
  }

  if (creditsSum == 0) return null;
  return weightedSum / creditsSum;
}

export function renderWeightedStudyAverage(hodnotenia: Hodnotenie[]) {
  const average = weightedStudyAverage(hodnotenia);
  if (average === null) return null;
  return (
    <span title="Neoficiálny vážený študijný priemer z doteraz ohodnotených predmetov">
      {average.toFixed(2)}
    </span>
  );
}

export function renderCredits({
  creditsObtained,
  creditsEnrolled,
}: {
  creditsObtained: number;
  creditsEnrolled: number;
}) {
  return creditsObtained && creditsObtained != creditsEnrolled
    ? `${creditsObtained}/${creditsEnrolled}`
    : `${creditsEnrolled}`;
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
