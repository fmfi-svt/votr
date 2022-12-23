import React from "react";

var ZNAMKY = { "A": 1, "B": 1.5, "C": 2, "D": 2.5, "E": 3, "F": 4 };

export function coursesStats(hodnotenia) {
  var result = {};

  ["zima", "leto", "spolu"].forEach((type) => {
    result[type] = { count: 0, creditsEnrolled: 0, creditsObtained: 0 };
  });

  function add(type, credits, obtained) {
    result[type].count++;
    result[type].creditsEnrolled += credits;
    result[type].creditsObtained += obtained ? credits : 0;
  }

  hodnotenia.forEach((row) => {
    var credits = parseInt(row.kredit);
    var obtained = row.hodn_znamka && row.hodn_znamka[0] !== "F";
    add("spolu", credits, obtained);
    if (row.semester == "Z") add("zima", credits, obtained);
    if (row.semester == "L") add("leto", credits, obtained);
  });

  return result;
}

export function weightedStudyAverage(hodnotenia) {
  var weightedSum = 0;
  var creditsSum = 0;

  hodnotenia.forEach((row) => {
    var value = ZNAMKY[row.hodn_znamka[0]];
    if (value) {
      weightedSum += value * parseInt(row.kredit);
      creditsSum += parseInt(row.kredit);
    }
  });

  if (creditsSum == 0) return null;
  return weightedSum / creditsSum;
}

export function renderWeightedStudyAverage(hodnotenia) {
  var average = weightedStudyAverage(hodnotenia);
  if (average === null) return null;
  return (
    <span title="Neoficiálny vážený študijný priemer z doteraz ohodnotených predmetov">
      {average.toFixed(2)}
    </span>
  );
}

export function renderCredits({ creditsObtained, creditsEnrolled }) {
  return creditsObtained && creditsObtained != creditsEnrolled
    ? `${creditsObtained}/${creditsEnrolled}`
    : `${creditsEnrolled}`;
}

export function currentAcademicYear() {
  var date = new Date();

  var year = date.getFullYear();
  var month = date.getMonth() + 1;

  if (month < 8) {
    return year - 1 + "/" + year;
  } else {
    return year + "/" + (year + 1);
  }
}
