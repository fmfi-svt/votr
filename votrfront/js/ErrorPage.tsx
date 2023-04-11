import React, { useState } from "react";
import { goLogout, goReset, goResetHome } from "./ajax";
import { Modal, ModalBase } from "./layout";
import { FakeLink } from "./router";

export function ErrorModal() {
  var [open, setOpen] = useState(false);

  function handleIgnore() {
    Votr.ajaxError = null;
    Votr.updateRoot();
  }

  function handleDetails() {
    setOpen(true);
  }

  var error = Votr.settings.error || Votr.ajaxError;
  var lastLine = error!.trim().replace(/.*\n/s, "");
  var type = lastLine.split(":")[0]!;

  var title = "Chyba";
  var description = "Vyskytla sa chyba a vaša požiadavka nebola spracovaná.";
  var contact = true;

  if (type == "aisikl.exceptions.LoggedOutError") {
    title = "Prihlásenie vypršalo";
    description = "Vaše prihlásenie vypršalo. Skúste znova.";
    contact = false;
  } else if (Votr.settings.error || type.match(/^requests\.exceptions\./)) {
    title = "Chyba pripojenia";
    description = "Votr sa nevie pripojiť na AIS.";
    contact = false;
  } else {
    if (type == "aisikl.exceptions.AISParseError") {
      description =
        "Votr nerozumie, čo spravil AIS. V novej verzii AISu sa asi niečo zmenilo.";
    }
    if (type == "aisikl.exceptions.AISBehaviorError") {
      if (lastLine.match(/args=\['(Nie je connection|Nastala SQL chyba)/)) {
        description = "AIS sa nevie pripojiť na svoju databázu.";
        contact = false;
      } else {
        description =
          "AIS spravil niečo nečakané a Votr si s tým nevie poradiť.";
      }
    }
  }

  // Some errors are caused by a malformed URL, so resetting won't help. If
  // we haven't navigated since the last full reload (the user has probably
  // reset just now), we redirect to the front page instead.
  var goHome =
    !Votr.didNavigate && !Votr.settings.error && location.search.substring(1);

  return (
    <Modal title={title} closeButton={false}>
      <p className="text-center">
        <big>{description}</big>
      </p>
      {contact && (
        <p className="text-center">
          Ak problém pretrváva, napíšte nám na{" "}
          <a href="mailto:fmfi-svt@googlegroups.com">
            fmfi-svt@googlegroups.com
          </a>
          .
        </p>
      )}
      <br />
      <ul className="list-inline text-center">
        {goHome ? (
          <li>
            <button
              type="button"
              className="btn btn-primary"
              onClick={goResetHome}
            >
              Späť na začiatok
            </button>
          </li>
        ) : (
          <li>
            <button type="button" className="btn btn-primary" onClick={goReset}>
              Skúsiť znova
            </button>
          </li>
        )}
        <li>
          <button type="button" className="btn btn-default" onClick={goLogout}>
            Odhlásiť
          </button>
        </li>
      </ul>
      <br />
      {open ? (
        <pre>{error}</pre>
      ) : (
        <p className="text-center text-muted">
          Technické detaily: <code>{lastLine}</code>{" "}
          <FakeLink onClick={handleDetails}>Viac detailov...</FakeLink>
        </p>
      )}
      {!Votr.settings.error && open && (
        <button
          type="button"
          className="btn btn-default"
          onClick={handleIgnore}
        >
          Ignorovať chybu
        </button>
      )}
    </Modal>
  );
}

export function ErrorPage() {
  return <ModalBase component={ErrorModal} onClose={() => {}} />;
}
