import React from "react";
import { Hodnotenie } from "./types";

var ZNAMKY: Record<string, number> = {
  "A": 1,
  "B": 1.5,
  "C": 2,
  "D": 2.5,
  "E": 3,
  "F": 4,
};

export function coursesStats(hodnotenia: Hodnotenie[]) {
  var result = {
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

  for (const row of hodnotenia) {
    var credits = parseInt(row.kredit);
    var obtained = !!row.hodn_znamka && row.hodn_znamka[0] !== "F";
    add("spolu", credits, obtained);
    if (row.semester == "Z") add("zima", credits, obtained);
    if (row.semester == "L") add("leto", credits, obtained);
  }

  return result;
}

export function weightedStudyAverage(hodnotenia: Hodnotenie[]) {
  var weightedSum = 0;
  var creditsSum = 0;

  for (const row of hodnotenia) {
    var value = ZNAMKY[row.hodn_znamka.charAt(0)];
    if (value) {
      weightedSum += value * parseInt(row.kredit);
      creditsSum += parseInt(row.kredit);
    }
  }

  if (creditsSum == 0) return null;
  return weightedSum / creditsSum;
}

export function renderWeightedStudyAverage(hodnotenia: Hodnotenie[]) {
  var average = weightedStudyAverage(hodnotenia);
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
  var date = new Date();

  var year = date.getFullYear();
  var month = date.getMonth() + 1;

  if (month < 8) {
    return `${year - 1}/${year}`;
  } else {
    return `${year}/${year + 1}`;
  }
}
