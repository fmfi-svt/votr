
import React from 'react';
import ReactDOM from 'react-dom';
import { ErrorPage } from './ErrorPage';
import { LoginPage } from './LoginPage';
import { App } from './actions';
import { Root } from './router';

import '../css/main.scss';


(function () {

if (!history.pushState || !window.Set || !window.Map || !Array.prototype.includes) {
  return;   // see prologue.js
}

window.addEventListener('error', function (event) {
  var { message, filename, lineno, colno, error } = event;
  var body = {
    message, filename, lineno, colno,
    errorString: '' + error,
    stack: error && error.stack,
    location: location.href,
  };
  var xhr = new XMLHttpRequest();
  xhr.open("POST", "report?type=onerror", true);
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.send(JSON.stringify(body));
}, false);
// TODO: Also deal with unhandledrejection.

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

var app =
    Votr.settings.servers ? LoginPage :
    Votr.settings.error ? ErrorPage :
    App;
var root = <Root app={app} />;

Votr.appRoot = ReactDOM.render(root, document.getElementById('votr'));


})();
