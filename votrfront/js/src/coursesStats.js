import React from 'react';

const ZNAMKY = {
  A: 1,
  B: 1.5,
  C: 2,
  D: 2.5,
  E: 3,
  F: 4,
};

export const coursesStats = (hodnotenia) => {
  const result = {};

  result.zima = {};
  result.zima.count = 0;
  result.zima.creditsCount = 0;

  result.leto = {};
  result.leto.count = 0;
  result.leto.creditsCount = 0;

  result.spolu = {};
  result.spolu.count = hodnotenia.length;
  result.spolu.creditsCount = 0;

  hodnotenia.forEach((row) => {
    let credits = parseInt(row.kredit, 10);
    if (row.hodn_znamka && row.hodn_znamka[0] === 'F') {
      credits = 0;
    }
    result.spolu.creditsCount += credits;
    if (row.semester === 'Z') {
      result.zima.count += 1;
      result.zima.creditsCount += credits;
    }
    if (row.semester === 'L') {
      result.leto.count += 1;
      result.leto.creditsCount += credits;
    }
  });

  return result;
};

export const weightedStudyAverage = (hodnotenia) => {
  let weightedSum = 0;
  let creditsSum = 0;

  hodnotenia.forEach((row) => {
    const value = ZNAMKY[row.hodn_znamka[0]];
    if (value) {
      weightedSum += value * parseInt(row.kredit, 10);
      creditsSum += parseInt(row.kredit, 10);
    }
  });

  if (creditsSum === 0) {
    return null;
  }
  return weightedSum / creditsSum;
};

export const renderWeightedStudyAverage = (hodnotenia) => {
  const average = weightedStudyAverage(hodnotenia);
  if (average === null) {
    return null;
  }
  return (
    <span title="Neoficiálny vážený študijný priemer z doteraz ohodnotených predmetov">
      {average.toFixed(2)}
    </span>
  );
};

export const currentAcademicYear = () => {
  const date = new Date();
  const year = date.getFullYear();
  const month = date.getMonth() + 1;

  if (month < 8) {
    return (year - 1) + '/' + year;
  } else {
    return year + '/' + (year + 1);
  }
};
