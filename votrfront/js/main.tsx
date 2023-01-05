import React from "react";
import { createRoot } from "react-dom/client";
import { ErrorPage } from "./ErrorPage";
import { LoginPage } from "./LoginPage";
import { App } from "./actions";
import { ErrorBoundary } from "./layout";
import { Root } from "./router";

import "../css/main.scss";

(function () {
  if (!Votr.prologueCheck) return; // see prologue.js

  window.addEventListener(
    "error",
    function (event) {
      var { message, filename, lineno, colno, error } = event;
      var body = {
        message,
        filename,
        lineno,
        colno,
        errorString: "" + error,
        stack: error && error.stack,
        location: location.href,
      };
      var xhr = new XMLHttpRequest();
      xhr.open("POST", "report?type=onerror", true);
      xhr.setRequestHeader("Content-Type", "application/json");
      xhr.send(JSON.stringify(body));
    },
    false
  );
  // TODO: Also deal with unhandledrejection.

  var query = Votr.settings.destination;
  if (query !== undefined && (query == "" || query.substring(0, 1) == "?")) {
    try {
      history.replaceState(null, "", Votr.settings.url_root + query);
    } catch (e) {
      console.error(e);
    }
  }

  var root = (
    <React.StrictMode>
      <ErrorBoundary>
        <Root
          app={
            Votr.settings.servers
              ? LoginPage
              : Votr.settings.error
              ? ErrorPage
              : App
          }
        />
      </ErrorBoundary>
    </React.StrictMode>
  );

  createRoot(document.getElementById("votr")!).render(root);
})();
