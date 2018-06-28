
var ZNAMKY = {'A': 1, 'B': 1.5, 'C': 2, 'D': 2.5, 'E': 3, 'F': 4};

export function coursesStats(hodnotenia) {
  var result = {};

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
    var credits = parseInt(row.kredit);
    if (row.hodn_znamka && row.hodn_znamka[0] === 'F') {
        credits = 0;
    }
    result.spolu.creditsCount += credits;
    if (row.semester == 'Z') {
      result.zima.count += 1;
      result.zima.creditsCount += credits;
    }
    if (row.semester == 'L') {
      result.leto.count += 1;
      result.leto.creditsCount += credits;
    }
  });

  return result;
};

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
};

export function renderWeightedStudyAverage(hodnotenia) {
  var average = weightedStudyAverage(hodnotenia);
  if (average === null) return null;
  return <span title="Neoficiálny vážený študijný priemer z doteraz ohodnotených predmetov">{average.toFixed(2)}</span>
};

export function currentAcademicYear() {
  var date = new Date();

  var year = date.getFullYear();
  var month = date.getMonth() + 1;

  if (month < 8) { 
    return (year - 1) + '/' + year;
  } else {
    return year + '/' + (year + 1);
  }
};
