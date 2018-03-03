import React from 'react';
import ReactDOM from 'react-dom';
import $ from 'jquery';

// TODO Remove these imports when Modals are implemented
// in our source with some package
import './libs/modal';
import './libs/transition';

import { ErrorPage } from './src/ErrorPage';
import { LoginPage } from './src/LoginPage';
import { App } from './src/actions';
import { Root } from './src/router';

// FIXME These are here just for their side effects, needs to be
// incorporated into source and deleted
import './src/prologue';
import './src/ovce';

(function() {
  window.$ = window.jQuery = $;
  if (!history.pushState) {
    // see prologue.js
    return;
  }

  //if (typeof __webpack_require__ !== 'undefined') {
  //  Votr.webpackRequire = __webpack_require__;
  //}

  const query = Votr.settings.destination;
  if (query !== undefined && (query === '' || query.substring(0, 1) === '?')) {
    try {
      history.replaceState(null, '', Votr.settings.url_root + query);
    } catch (e) {
      console.error(e);
    }
  }

  let root = <Root app={App} />;
  if (Votr.settings.servers) {
    root = <LoginPage />;
  } else if (Votr.settings.error) {
    root = <ErrorPage />;
  }

  Votr.appRoot = ReactDOM.render(root, document.getElementById('votr'));
})();
