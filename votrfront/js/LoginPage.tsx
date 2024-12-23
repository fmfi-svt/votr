import React, { useContext, useState } from "react";
import { AboutModal } from "./About";
import { actionTitles } from "./actions";
import { Announcement, Modal, ModalBase } from "./layout";
import { getLocalSetting, setLocalSetting } from "./LocalSettings";
import { buildUrl, FakeLink, QueryContext } from "./router";

const TYPE_NAMES: Record<string, string> = {
  "saml_andrvotr": "SAML + Andrvotr",
  "saml_password": "SAML + meno a heslo",
  "cookie": "Manuálne cookie",
  "plain_password": "Meno a heslo",
  "flashback": "Flashback",
};

function DestinationCheckbox() {
  const query = useContext(QueryContext);
  const { action, modal } = query;
  const actionTitle = action && actionTitles[action];

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
  const [state, setState] = useState({
    server: Votr.settings.server || 0,
    type: Votr.settings.type,
  });

  function handleServerChange(event: React.ChangeEvent<HTMLSelectElement>) {
    const server = Number(event.target.value);
    const newTypes = Votr.settings.servers![server]!.login_types;
    setState((old) => ({
      server,
      type: old.type && newTypes.includes(old.type) ? old.type : null,
    }));
  }

  function handleTypeChange(event: React.ChangeEvent<HTMLSelectElement>) {
    const type = event.target.value;
    setState((old) => ({ server: old.server, type }));
  }

  const serverConfig = Votr.settings.servers![state.server]!;
  const currentType = state.type || serverConfig.login_types[0];

  return (
    <form className="login" action="login" method="POST" rel="nofollow">
      {Votr.settings.invalid_session && (
        <p>Vaše prihlásenie vypršalo. Prihláste sa znova.</p>
      )}

      {!!Votr.settings.error && (
        <React.Fragment>
          <p>Prihlásenie sa nepodarilo.</p>
          <p>
            {"Technické detaily: "}
            <code className="login-error">
              {Votr.settings.error.trim().replace(/[\s\S]*\n/, "")}
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

      {(currentType == "saml_password" || currentType == "plain_password") && (
        <React.Fragment>
          <details>
            <summary>Bezpečnostné informácie</summary>
            <p>Toto nie je oficiálny univerzitný prihlasovací formulár.</p>
            <p>
              Spravidla nie je bezpečné prezradiť vaše heslo z jednej stránky
              druhému človeku alebo stránke. Mohol by nežiaduco konať vo vašom
              mene, skúšať rovnaké heslo aj na iných stránkach, alebo vás
              vymknúť z účtu.
            </p>
            <p>
              Autori Votru sa zaväzujú, že vaše univerzitné heslo a účet nijako
              nezneužijú, ale v záujme transparentnosti vás chcú upozorniť na
              toto potenciálne riziko.
            </p>
          </details>
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

      {currentType == "cookie" && (
        <React.Fragment>
          <p>
            <strong>Pokyny:</strong> Prihláste sa do AISu. Pomocou vývojárskych
            nástrojov vytiahnite z AISu hodnotu vášho prihlasovacieho cookie a
            skopírujte ju sem.
          </p>
          <ul>
            <li>
              Chrome: F12 &#x2192; Application &#x2192; Storage &#x2192; Cookies
            </li>
            <li>Firefox: F12 &#x2192; Storage &#x2192; Cookies</li>
            <li>iOS/Android: smola :(</li>
          </ul>
          <p>
            <strong>Efekt:</strong> Dáte tým Votru dočasné splnomocnenie
            pristupovať k AISu vo vašom mene. (Platí iba krátku dobu a iba do
            AISu.)
          </p>
          {!!serverConfig.ais_cookie && (
            <p>
              <label>
                Hodnota cookie <code>{serverConfig.ais_cookie}</code> na{" "}
                <a
                  href={serverConfig.ais_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {serverConfig.ais_url}
                </a>
                : <input name="ais_cookie" />
              </label>
            </p>
          )}
          {!!serverConfig.rest_cookie && (
            <p>
              <label>
                Hodnota cookie <code>{serverConfig.rest_cookie}</code> na{" "}
                <a
                  href={serverConfig.rest_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {serverConfig.rest_url}
                </a>
                : <input name="rest_cookie" />
              </label>
            </p>
          )}
          <p>
            V prípade potreby je možné zadať aj viacero cookies (
            <code>meno=hodnota; meno=hodnota</code>).
          </p>
        </React.Fragment>
      )}

      {currentType == "flashback" && (
        <p>
          <label>
            {"Súbor: "}
            <select name="file">
              <option value=""></option>
              {(serverConfig.flashback_files || []).map((name, index) => (
                <option key={index} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </label>
        </p>
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
  const [modal, setModal] = useState<React.ComponentType | null>(null);

  return (
    <React.Fragment>
      <div className="login-page">
        <div className="navbar navbar-inverse navbar-static-top">
          <div className="container-fluid">
            <div className="navbar-header">
              <a href={Votr.settings.url_root} className="navbar-brand">
                {Votr.settings.instance_title}
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
                rel="noopener noreferrer"
              >
                Univerzita Komenského
              </a>
            </li>
            <li>
              <a
                className="btn btn-link"
                href="https://moja.uniba.sk/"
                target="_blank"
                rel="noopener noreferrer"
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
