/** @jsx React.DOM */

(function () {


var TYPY_VYUCBY = {
  'A': 'povinné (A)',
  'B': 'povinne voliteľné (B)',
  'C': 'výberové (C)'
};

var TERMIN_HODNOTENIA = {
  'R - Riadny termín': 'riadny',
  '1 - Prvý opravný termín': 'prvý opravný',
  '2 - Druhý opravný termín': 'druhý opravný'
};

Votr.humanizeTypVyucby = function (skratka) {
  return TYPY_VYUCBY[skratka] || skratka;
};

Votr.humanizeTerminHodnotenia = function (skratka) {
  return TERMIN_HODNOTENIA[skratka] || skratka;
};

})();
