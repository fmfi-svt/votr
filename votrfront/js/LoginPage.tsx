import React, { useContext, useState } from "react";
import { AboutModal } from "./About";
import { actionTitles } from "./actions";
import { Announcement, Modal, ModalBase } from "./layout";
import { getLocalSetting, setLocalSetting } from "./LocalSettings";
import { buildUrl, FakeLink, QueryContext } from "./router";

var TYPE_NAMES: Record<string, string> = {
  "cosignproxy": "Cosign (automatické)",
  "cosignpassword": "Cosign (meno a heslo)",
  "cosigncookie": "Cosign (manuálne cookie)",
  "plainpassword": "Meno a heslo",
  "demo": "Demo",
};

function DestinationCheckbox() {
  var query = useContext(QueryContext);
  var { action, modal } = query;
  var actionTitle = action && actionTitles[action];

  // Don't show the checkbox if the query string is empty or it only contains
  // foreign params (?fbclid=...).
  if (!action && !modal) return null;

  return (
    <p>
      <label>
        <input
          type="checkbox"
          name="destination"
          value={buildUrl(query)}
          checked={getLocalSetting("useDestination") == "true"}
          onChange={(event) => {
            setLocalSetting("useDestination", String(event.target.checked));
          }}
        />{" "}
        Začať tam kde predtým {actionTitle ? "(" + actionTitle + ") " : null}
        podľa uloženej webovej adresy
      </label>
    </p>
  );
}

function LoginForm({ onOpenError }: { onOpenError: () => void }) {
  var [state, setState] = useState({
    server: Votr.settings.server || 0,
    type: Votr.settings.type,
  });

  function handleServerChange(event: React.ChangeEvent<HTMLSelectElement>) {
    var server = Number(event.target.value);
    var newTypes = Votr.settings.servers![server]!.login_types;
    setState((old) => ({
      server,
      type: old.type && newTypes.includes(old.type) ? old.type : null,
    }));
  }

  function handleTypeChange(event: React.ChangeEvent<HTMLSelectElement>) {
    var type = event.target.value;
    setState((old) => ({ server: old.server, type }));
  }

  var serverConfig = Votr.settings.servers![state.server]!;
  var currentType = state.type || serverConfig.login_types[0];

  return (
    <form className="login" action="login" method="POST">
      {Votr.settings.invalid_session && (
        <p>Vaše prihlásenie vypršalo. Prihláste sa znova.</p>
      )}

      {!!Votr.settings.error && (
        <React.Fragment>
          <p>Prihlásenie sa nepodarilo.</p>
          <p>
            {"Technické detaily: "}
            <code className="login-error">
              {Votr.settings.error.trim().replace(/.*\n/s, "")}
            </code>{" "}
            <FakeLink onClick={onOpenError}>Viac detailov...</FakeLink>
          </p>
          <p>
            Ak problém pretrváva, napíšte nám na{" "}
            <a className="text-nowrap" href="mailto:fmfi-svt@googlegroups.com">
              fmfi-svt@googlegroups.com
            </a>
            .
          </p>
          <hr />
        </React.Fragment>
      )}

      <DestinationCheckbox />

      {Votr.settings.servers!.length > 1 ? (
        <p>
          <label>
            {"Server: "}
            <select
              name="server"
              value={state.server}
              onChange={handleServerChange}
            >
              {Votr.settings.servers!.map((server, index) => (
                <option key={index} value={index}>
                  {server.title}
                </option>
              ))}
            </select>
          </label>
        </p>
      ) : (
        <input type="hidden" name="server" value="0" />
      )}

      {serverConfig.login_types.length > 1 ? (
        <p>
          <label>
            {"Typ prihlásenia: "}
            <select name="type" value={currentType} onChange={handleTypeChange}>
              {serverConfig.login_types.map((type) => (
                <option key={type} value={type}>
                  {TYPE_NAMES[type]}
                </option>
              ))}
            </select>
          </label>
        </p>
      ) : (
        <input type="hidden" name="type" value={currentType} />
      )}

      {(currentType == "cosignpassword" || currentType == "plainpassword") && (
        <React.Fragment>
          <p>
            <label>
              {"Meno: "}
              <input name="username" />
            </label>
          </p>
          <p>
            <label>
              {"Heslo: "}
              <input name="password" type="password" />
            </label>
          </p>
        </React.Fragment>
      )}

      {currentType == "cosigncookie" && (
        <React.Fragment>
          {/* TODO: Detailed instructions for cosigncookie. */}
          {!!serverConfig.ais_cookie && (
            <p>
              <label>
                {"Hodnota cookie " + serverConfig.ais_cookie + ": "}
                <input name="ais_cookie" />
              </label>
            </p>
          )}
          {!!serverConfig.rest_cookie && (
            <p>
              <label>
                {"Hodnota cookie " + serverConfig.rest_cookie + ": "}
                <input name="rest_cookie" />
              </label>
            </p>
          )}
        </React.Fragment>
      )}

      <button type="submit" className="btn btn-lg btn-primary center-block">
        Prihlásiť
      </button>
    </form>
  );
}

function LoginErrorModal() {
  return (
    <Modal title="Chyba pri prihlásení">
      <pre>{Votr.settings.error}</pre>
    </Modal>
  );
}

export function LoginPage() {
  var [modal, setModal] = useState<React.ComponentType | null>(null);

  return (
    <React.Fragment>
      <div className="login-page">
        <div className="navbar navbar-inverse navbar-static-top">
          <div className="container-fluid">
            <div className="navbar-header">
              <a href={Votr.settings.url_root} className="navbar-brand">
                Votr
              </a>
            </div>
          </div>
        </div>
        <div className="login-content">
          <p>
            <strong>Votr</strong> ponúka študentom jednoduchší a pohodlnejší
            spôsob, ako robiť najčastejšie činnosti zo systému AIS. Zapíšte sa
            na skúšky, prezrite si vaše hodnotenia a skontrolujte si počet
            kreditov bez zbytočného klikania.
          </p>
          <Announcement />
          <hr />
          <LoginForm onOpenError={() => setModal(() => LoginErrorModal)} />
        </div>
        <div className="text-center">
          <ul className="list-inline">
            <li>
              <FakeLink
                className="btn btn-link"
                onClick={() => setModal(() => AboutModal)}
              >
                O aplikácii
              </FakeLink>
            </li>
            <li>
              <a
                className="btn btn-link"
                href="https://uniba.sk/"
                target="_blank"
              >
                Univerzita Komenského
              </a>
            </li>
            <li>
              <a
                className="btn btn-link"
                href="https://moja.uniba.sk/"
                target="_blank"
              >
                IT služby na UK
              </a>
            </li>
          </ul>
        </div>
      </div>

      <ModalBase component={modal} onClose={() => setModal(null)} />
    </React.Fragment>
  );
}
