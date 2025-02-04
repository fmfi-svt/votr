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
    (event) => {
      const { message, filename, lineno, colno } = event;
      const error: unknown = event.error;
      reportClientError("onerror", {
        message,
        filename,
        lineno,
        colno,
        errorString: String(error),
        stack: error && (error as { stack?: unknown }).stack,
      });
    },
    false,
  );
  window.addEventListener(
    "unhandledrejection",
    (event) => {
      const error: unknown = event.reason;
      reportClientError("unhandledrejection", {
        errorString: String(error),
        stack: error && (error as { stack?: unknown }).stack,
      });
    },
    false,
  );

  const query = Votr.settings.destination;
  if (query !== undefined && (query == "" || query.startsWith("?"))) {
    try {
      history.replaceState(null, "", Votr.settings.url_root + query);
    } catch (e) {
      console.error(e);
    }
  }

  const root = (
    <React.StrictMode>
      <ErrorBoundary>
        <Root
          app={
            Votr.settings.servers ? LoginPage
            : Votr.settings.error ?
              ErrorPage
            : App
          }
        />
      </ErrorBoundary>
    </React.StrictMode>
  );

  createRoot(document.getElementById("votr")!).render(root);
})();
