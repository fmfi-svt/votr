/**
 * @jsx React.DOM
 * @dontdepend Votr.settings
 * @dontdepend Votr.appRoot
 */

(function () {

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

if (Votr.settings.servers) {
  Votr.appRoot = React.renderComponent(Votr.LoginPage(), document.getElementById('votr'));
  return;
}

if (Votr.settings.error) {
  var el = document.getElementById('votr');
  $('<h1/>').text('Error').appendTo(el);
  $('<pre/>').text(Votr.settings.error).appendTo(el);
  // TODO HARDRESET button
  // TODO LOGOUT button
  return;
}

Votr.appRoot = React.renderComponent(<Votr.Root app={Votr.App} />, document.getElementById('votr'));


})();
