/** @jsx React.DOM */

(function () {

function humanizeWith(table) {
  return function (value) {
    return table[value] || value;
  }
}

Votr.humanizeTypVyucby = humanizeWith({
  'A': 'povinné (A)',
  'B': 'povinne voliteľné (B)',
  'C': 'výberové (C)'
});

Votr.humanizeTerminHodnotenia = humanizeWith({
  'R - Riadny termín': 'riadny',
  '1 - Prvý opravný termín': 'prvý opravný',
  '2 - Druhý opravný termín': 'druhý opravný'
});

Votr.humanizeNazovPriemeru = humanizeWith({
  'Sem ?': 'Semester',
  'AkadR ?' : 'Akademický rok'
});

Votr.humanizeBoolean = humanizeWith({
  'A': 'áno',
  'N': 'nie'
});

Votr.classForSemester = function (semester) {
  if (semester == 'Z') return 'zima';
  if (semester == 'L') return 'leto';
  return undefined;
};

})();
