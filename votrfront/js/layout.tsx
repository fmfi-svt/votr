import $ from "jquery";
import { last } from "lodash-es";
import React, { useContext, useEffect, useRef } from "react";

import "bootstrap-sass/assets/javascripts/bootstrap/transition"; // needed by modal.js.

import "bootstrap-sass/assets/javascripts/bootstrap/modal"; // needed for $node.modal().

import {
  ajaxLogs,
  CacheRequester,
  goLogout,
  goReset,
  goResetHome,
  Loading,
  reportClientError,
} from "./ajax";
import { AnketaPopup } from "./AnketaPopup";
import { FakeLink, Link, QueryContext, RelativeLink } from "./router";
import { Href } from "./types";

export class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { error: unknown; open: boolean }
> {
  override state: { error: unknown; open: boolean } = {
    error: undefined,
    open: false,
  };

  override componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    setTimeout(function () {
      console.error("ErrorBoundary caught error:", [error, errorInfo]);
      reportClientError("errorboundary", {
        errorString: String(error),
        // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition, @typescript-eslint/prefer-optional-chain
        stack: error && error.stack,
        componentStack: errorInfo.componentStack,
      });
    }, 0);
  }

  static getDerivedStateFromError(error: unknown) {
    return { error: error };
  }

  handleDetails = () => {
    this.setState({ open: true });
  };

  override render() {
    if (this.state.error) {
      var error = this.state.error;
      var details = String(
        (typeof error == "object" && "stack" in error && error.stack) || error
      );
      var firstLine = details.trim().split("\n")[0];
      return (
        <div className="alert alert-danger">
          <h3>Chyba</h3>
          <p>Vyskytla sa chyba a túto stránku nebolo možné zobraziť.</p>
          <p>
            Ak problém pretrváva, napíšte nám na{" "}
            <a href="mailto:fmfi-svt@googlegroups.com">
              fmfi-svt@googlegroups.com
            </a>
            .
          </p>
          <br />
          <ul className="list-inline">
            <li>
              <button
                type="button"
                className="btn btn-primary"
                onClick={goResetHome}
              >
                Späť na začiatok
              </button>
            </li>
            <li>
              <button
                type="button"
                className="btn btn-default"
                onClick={goLogout}
              >
                Odhlásiť
              </button>
            </li>
          </ul>
          <br />
          {this.state.open ? (
            <pre>{details}</pre>
          ) : (
            <p className="text-muted">
              Technické detaily: <code>{firstLine}</code>{" "}
              <FakeLink onClick={this.handleDetails}>Viac detailov...</FakeLink>
            </p>
          )}
        </div>
      );
    } else {
      return this.props.children;
    }
  }
}

export function Announcement() {
  const announcement = Votr.settings.announcement_html;
  if (!announcement) return null;
  return (
    <p
      className="alert alert-warning"
      role="alert"
      dangerouslySetInnerHTML={{ __html: announcement }}
    />
  );
}

export function PageLayout(props: { children: React.ReactNode }) {
  return (
    <React.Fragment>
      <PageNavbar />
      <div className="layout-container">
        <div className="layout-menu">
          <MainMenu />
        </div>
        <div className="layout-content">
          <div className="container-fluid">
            <ErrorBoundary>
              <AnketaPopup />
              <Announcement />
              {props.children}
            </ErrorBoundary>
          </div>
        </div>
      </div>
    </React.Fragment>
  );
}

function PageNavbar() {
  return (
    <div className="navbar navbar-inverse navbar-static-top">
      <div className="container-fluid">
        <div className="navbar-header">
          <Link className="navbar-brand" href={{}}>
            Votr
          </Link>
        </div>
        <div className="navbar-left">
          <LogStatus />
        </div>
        <div className="navbar-right">
          <ul className="nav navbar-nav">
            <li>
              <RelativeLink href={{ modal: "about" }}>O aplikácii</RelativeLink>
            </li>
            <li>
              <FakeLink onClick={goReset} title="Znovu načítať všetky dáta">
                Obnoviť
              </FakeLink>
            </li>
            <li>
              <FakeLink onClick={goLogout}>Odhlásiť</FakeLink>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}

function LogStatus() {
  var entry = last(ajaxLogs);
  var message;
  if (!entry) {
    message = "\xA0"; // nbsp
  } else if (entry.log == "http" && entry.message.match(/^Requesting/)) {
    message = "Čakám na AIS...";
  } else if (entry.log == "rpc" && entry.message.match(/finished$/)) {
    message = "\xA0"; // nbsp
  } else {
    message = "Spracovávam dáta... (" + entry.message + ")";
  }
  return <p className="navbar-text">{message}</p>;
}

export function PageTitle({ children }: { children: React.ReactNode }) {
  var titleRef = useRef<HTMLHeadingElement | null>(null);

  useEffect(() => {
    document.title = titleRef.current!.textContent!;
  });

  return <h1 ref={titleRef}>{children}</h1>;
}

function MenuItem(props: {
  active?: boolean;
  href: Href;
  label: React.ReactNode;
}) {
  var query = useContext(QueryContext);
  var isActive = props.active || props.href.action == query.action;
  return (
    <li className={isActive ? "active" : undefined}>
      <Link href={props.href}>{props.label}</Link>
    </li>
  );
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function DisabledItem(props: { label: React.ReactNode }) {
  // return <li className="disabled"><a>{props.label}</a></li>;
  return null;
}

function MainMenu() {
  var query = useContext(QueryContext);
  var { action, studiumKey, zapisnyListKey } = query;

  var cache = new CacheRequester();
  var somStudent = cache.get("get_som_student");

  return (
    <ul className="main-menu nav nav-pills nav-stacked">
      <li>
        <strong className="text-pill">Moje štúdium</strong>
      </li>
      {somStudent === false && (
        <li>
          <span className="text-pill">Nie ste študentom.</span>
        </li>
      )}
      {somStudent && (
        <React.Fragment>
          <MenuItem
            label="Moje predmety"
            href={{ action: "mojePredmety", zapisnyListKey }}
          />
          <MenuItem
            label="Moje skúšky"
            href={{ action: "mojeSkusky", zapisnyListKey }}
          />
          <MenuItem
            label="Moje hodnotenia"
            href={{ action: "mojeHodnotenia", studiumKey }}
          />
          <MenuItem
            label="Priebežné hodnotenia"
            href={{ action: "priebezneHodnotenia", zapisnyListKey }}
          />
          <DisabledItem label="Môj rozvrh" />
          <MenuItem
            label="Zápis predmetov"
            href={{ action: "zapisZPlanu", zapisnyListKey }}
            active={action == "zapisZPonuky"}
          />
          <MenuItem label="Prehľad štúdia" href={{ action: "prehladStudia" }} />
        </React.Fragment>
      )}
      {!cache.loadedAll && (
        <li>
          <span className="text-pill">
            <Loading requests={cache.missing} />
          </span>
        </li>
      )}
      <li>
        <hr />
      </li>
      <li>
        <strong className="text-pill">Registre</strong>
      </li>
      <MenuItem label="Register osôb" href={{ action: "registerOsob" }} />
      <MenuItem
        label="Register predmetov"
        href={{ action: "registerPredmetov" }}
      />
      <DisabledItem label="Register miestností" />
      <DisabledItem label="Register študijných programov" />
      {!!Votr.settings.feedback_link && (
        <>
          <li>
            <hr />
          </li>
          <li>
            <a href={Votr.settings.feedback_link} target="_blank">
              Poslať feedback
            </a>
          </li>
        </>
      )}
    </ul>
  );
}

export function FormItem(props: {
  label?: React.ReactNode;
  children: React.ReactNode;
}) {
  if (props.label) {
    return (
      <label className="form-item">
        <div className="col-sm-4 form-item-label">{props.label}</div>
        <div className="col-sm-8">{props.children}</div>
      </label>
    );
  } else {
    return (
      <div className="form-item">
        <div className="col-sm-offset-4 col-sm-8">{props.children}</div>
      </div>
    );
  }
}

export function ModalBase({
  onClose,
  component,
}: {
  onClose: () => void;
  component: React.ComponentType | undefined | null;
}) {
  var modalRef = useRef<HTMLDivElement | null>(null);

  var C = component;
  const open = !!C;

  // This is so dumb.
  // TODO: "useEffectEvent" might simplify this in a future React version.
  var closeHandlerRef = useRef<((e: JQuery.Event) => void) | null>(null);
  useEffect(() => {
    closeHandlerRef.current = (e) => {
      if (open) {
        e.preventDefault();
        onClose();
      }
    };
  }, [onClose, open]);

  useEffect(() => {
    var $node = $(modalRef.current!);
    $node.modal();
    var handler = (e: JQuery.Event) => {
      closeHandlerRef.current!(e);
    };
    $node.on("hide.bs.modal", handler);
    return () => {
      $node.off("hide.bs.modal", handler);
    };
  }, []);

  useEffect(() => {
    var $node = $(modalRef.current!);
    $node.modal(open ? ("show" as const) : ("hide" as const));
  }, [open]);

  return (
    <div
      className="modal fade"
      ref={modalRef}
      tabIndex={-1}
      role="dialog"
      aria-hidden="true"
    >
      <div className="modal-dialog modal-lg">
        {!!C && (
          <ErrorBoundary>
            <C />
          </ErrorBoundary>
        )}
      </div>
    </div>
  );
}

export function Modal({
  closeButton = true,
  title,
  children,
}: {
  closeButton?: boolean;
  title: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="modal-content">
      <div className="modal-header">
        {closeButton && (
          <button type="button" className="close" data-dismiss="modal">
            <span aria-hidden="true">&times;</span>
            <span className="sr-only">Close</span>
          </button>
        )}
        <h4 className="modal-title">{title}</h4>
      </div>
      <div className="modal-body">
        <ErrorBoundary>{children}</ErrorBoundary>
      </div>
    </div>
  );
}
