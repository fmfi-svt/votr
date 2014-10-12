/** @jsx React.DOM */

(function () {

var ZNAMKY = {'A': 1, 'B': 1.5, 'C': 2, 'D': 2.5, 'E': 3, 'F': 4};

Votr.coursesStats = function (hodnotenia) {
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
    result.spolu.creditsCount += credits;
    if (row.semester == 'Z') {
      result.zima.count += 1;
      result.zima.creditsCount += credits;
    } else {
      result.leto.count += 1;
      result.leto.creditsCount += credits;
    }
  });

  return result;
};

Votr.weightedStudyAverage = function (hodnotenia) {
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

Votr.renderWeightedStudyAverage = function (hodnotenia) {
  var average = Votr.weightedStudyAverage(hodnotenia);
  if (average === null) return null;
  return <span title="Neoficiálny vážený študijný priemer z doteraz ohodnotených predmetov">{average.toFixed(2)}</span>
};

})();
