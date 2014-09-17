/**
 * @require jquery.min.js
 * @require lodash.min.js
 * @require react.min.js
 * @require LoginPage.js
 * @require ajax.js
 * @require router.js
 * @require layout.js
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

Votr.actions['index'] = React.createClass({
  render: function () {
    var cache = new Votr.CacheRequester();
    var studia = cache.get('get_studia');
    var studiaResult = studia ? JSON.stringify(studia) : Votr.Loading({requests: cache.missing});
    return Votr.PageLayout({query: this.props.query}, React.DOM.div(null, "Index page", studiaResult));
  }
});

Votr.appRoot = React.renderComponent(Votr.App(), document.getElementById('votr'));


})();
