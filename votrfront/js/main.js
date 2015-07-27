
import { ErrorPage } from './ErrorPage';
import { LoginPage } from './LoginPage';
import { App } from './actions';
import { Root } from './router';


(function () {

if (!history.pushState) {
  return;   // see old.js
}

if (typeof __webpack_require__ !== 'undefined') {
  Votr.webpackRequire = __webpack_require__;
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
    Votr.settings.servers ? <LoginPage /> :
    Votr.settings.error ? <ErrorPage /> :
    <Root app={App} />;

Votr.appRoot = React.render(root, document.getElementById('votr'));


})();
