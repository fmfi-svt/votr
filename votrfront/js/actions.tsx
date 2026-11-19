import { omitBy } from "lodash-es";
import React, { useContext } from "react";
import { AboutModal, makeIndexPage } from "./About";
import { DetailPredmetuModal } from "./DetailPredmetu";
import { ErrorModal } from "./ErrorPage";
import { ModalBase, PageLayout } from "./layout";
import { LogViewer } from "./LogViewer";
import { makeMojeHodnoteniaPage } from "./MojeHodnoteniaPage";
import { makeMojePredmetyPage } from "./MojePredmetyPage";
import { makeMojeSkuskyPage } from "./MojeSkuskyPage";
import { makePrehladStudiaPage } from "./PrehladStudiaPage";
import { makePriebezneHodnoteniaPage } from "./PriebezneHodnoteniaPage";
import { makeRegisterOsobPage } from "./RegisterOsobPage";
import { makeRegisterPredmetovPage } from "./RegisterPredmetovPage";
import { navigate, QueryContext } from "./router";
import { makeZapisZPlanuPage, makeZapisZPonukyPage } from "./ZapisPage";
import { ZoznamPrihlasenychNaTerminModal } from "./ZoznamPrihlasenychNaTermin";

function makeNotFoundPage() {
  return (
    <PageLayout>
      <p>Action not found!</p>
    </PageLayout>
  );
}

const actions = new Map(
  Object.entries({
    priebezneHodnotenia: makePriebezneHodnoteniaPage,
    mojeHodnotenia: makeMojeHodnoteniaPage,
    mojePredmety: makeMojePredmetyPage,
    mojeSkusky: makeMojeSkuskyPage,
    prehladStudia: makePrehladStudiaPage,
    registerOsob: makeRegisterOsobPage,
    registerPredmetov: makeRegisterPredmetovPage,
    zapisZPlanu: makeZapisZPlanuPage,
    zapisZPonuky: makeZapisZPonukyPage,
  }),
);

// TODO: Reduce code duplication of page titles.
// TODO: Set document.title immediately even if a ...Selector is loading.
export const actionTitles = new Map(
  Object.entries({
    priebezneHodnotenia: "Priebežné hodnotenia",
    mojeHodnotenia: "Moje hodnotenia",
    mojePredmety: "Moje predmety",
    mojeSkusky: "Moje skúšky",
    prehladStudia: "Prehľad štúdia",
    registerOsob: "Register osôb",
    registerPredmetov: "Register predmetov",
    zapisZPlanu: "Zápis predmetov",
    zapisZPonuky: "Zápis predmetov",
  }),
);

const modalActions = new Map(
  Object.entries({
    about: AboutModal,
    detailPredmetu: DetailPredmetuModal,
    zoznamPrihlasenychNaTermin: ZoznamPrihlasenychNaTerminModal,
  }),
);

export function App() {
  const query = useContext(QueryContext);
  const action = query.action;
  const maker =
    action ? actions.get(action) || makeNotFoundPage : makeIndexPage;
  const modalComponent =
    Votr.ajaxError ? ErrorModal
    : query.modal ? modalActions.get(query.modal)
    : undefined;

  function handleClose() {
    if (Votr.ajaxError) return;
    navigate(omitBy(query, (value, key) => key.startsWith("modal")));
  }

  return (
    <React.Fragment>
      {maker()}
      <ModalBase component={modalComponent} onClose={handleClose} />
      <LogViewer />
    </React.Fragment>
  );
}
