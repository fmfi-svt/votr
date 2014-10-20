/** @jsx React.DOM */

(function () {


Votr.LocalSettings = {
  get: function (key) {
    return localStorage.getItem(Votr.settings.instance_name + "_" + key);
  },

  set: function (key, value) {
    localStorage.setItem(Votr.settings.instance_name + "_" + key, value);
    Votr.appRoot.forceUpdate();
  }
};


})();
