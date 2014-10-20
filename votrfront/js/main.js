/**
 * @jsx React.DOM
 * @dontdepend Votr.settings
 * @dontdepend Votr.appRoot
 */

(function () {

if (!history.pushState) {
  return;   // see old.js
}

var query = Votr.settings.destination;
if (query !== undefined && (query == '' || query.substring(0, 1) == '?')) {
  try {
    history.replaceState(null, '', Votr.settings.url_root + query);
  } catch (e) {
    console.error(e);
  }
}

Votr.setDebug = function (enabled) {
  document.cookie = enabled ? 'votr_debug=true' : 'votr_debug=';
  location.reload();
}

var root =
    Votr.settings.servers ? <Votr.LoginPage /> :
    Votr.settings.error ? <Votr.ErrorPage /> :
    <Votr.Root app={Votr.App} />;

Votr.appRoot = React.renderComponent(root, document.getElementById('votr'));


})();
