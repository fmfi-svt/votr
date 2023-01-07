import React from "react";
import { createRoot } from "react-dom/client";
import { App } from "./actions";
import { reportClientError } from "./ajax";
import { ErrorPage } from "./ErrorPage";
import { ErrorBoundary } from "./layout";
import { LoginPage } from "./LoginPage";
import { Root } from "./router";

import "../css/main.scss";

(function () {
  if (!Votr.prologueCheck) return; // see prologue.js

  window.addEventListener(
    "error",
    function (event) {
      var { message, filename, lineno, colno, error } = event;
      reportClientError("onerror", {
        message,
        filename,
        lineno,
        colno,
        errorString: "" + error,
        stack: error && error.stack,
      });
    },
    false
  );
  window.addEventListener(
    "unhandledrejection",
    function (event) {
      var error: unknown = event.reason;
      reportClientError("unhandledrejection", {
        errorString: "" + error,
        stack: error && (error as { stack: unknown }).stack,
      });
    },
    false
  );

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
