
import React from 'react';
import ReactDOM from 'react-dom';
import { ErrorPage } from './ErrorPage';
import { LoginPage } from './LoginPage';
import { App } from './actions';
import { Root } from './router';
import { settings } from './settings';

import '../css/main.scss';


if (Votr.go) {

if (typeof __webpack_require__ !== 'undefined') {
  Votr.webpackRequire = __webpack_require__;
}

var query = settings.destination;
if (query !== undefined && (query == '' || query.substring(0, 1) == '?')) {
  try {
    history.replaceState(null, '', settings.url_root + query);
  } catch (e) {
    console.error(e);
  }
}

var app =
    settings.servers ? LoginPage :
    settings.error ? ErrorPage :
    App;
var root = <Root app={app} />;

Votr.appRoot = ReactDOM.render(root, document.getElementById('votr'));

}
