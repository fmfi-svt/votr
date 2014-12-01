/**
 * @jsx React.DOM
 * @dontdepend Votr.settings
 * @dontdepend Votr.appRoot
 */

(function () {

if (!history.pushState) {
  // Use onload because IE8 reorders the main.js script tag before the div.
  window.onload = function () {
    document.getElementById('votr').innerHTML = (
      '<div class="central-box">'+
      '<h1>Votr</h1>'+
      '<p>Votr ponúka študentom jednoduchší a pohodlnejší spôsob, ako robiť najčastejšie činnosti zo systému AIS.</p>'+
      '<p>Váš prehliadač je príliš starý a nedokáže robiť všetko to, čo Votr potrebuje.</p>'+
      '<p>Prosím stiahnite si novší prehliadač. Nové prehliadače sú rýchlejšie, pohodlnejšie a navyše bezpečnejšie.</p>'+
      '<br>'+
      '<ul class="list-inline">'+
      '<li><a class="btn btn-link" href="https://www.firefox.com/">Mozilla Firefox</a>'+
      '<li><a class="btn btn-link" href="https://www.google.com/chrome">Google Chrome</a>'+
      '<li><a class="btn btn-link" href="https://www.opera.com/">Opera</a>'+
      '<li><a class="btn btn-link" href="https://www.apple.com/safari/">Safari</a>'+
      '<li><a class="btn btn-link" href="http://windows.microsoft.com/ie">Internet Explorer (10+)</a>'+
      '</ul>'+
      '</div>');
  };
  return;
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
