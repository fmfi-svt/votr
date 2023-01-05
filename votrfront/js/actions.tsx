import React, { useContext } from "react";
import _ from "lodash";
import { AboutModal, makeIndexPage } from "./About";
import { DetailPredmetuModal } from "./DetailPredmetu";
import { ErrorModal } from "./ErrorPage";
import { LogViewer } from "./LogViewer";
import { makeMojeHodnoteniaPage } from "./MojeHodnoteniaPage";
import { makePriebezneHodnoteniaPage } from "./PriebezneHodnoteniaPage";
import { makeMojePredmetyPage } from "./MojePredmetyPage";
import { makeMojeSkuskyPage } from "./MojeSkuskyPage";
import { makePrehladStudiaPage } from "./PrehladStudiaPage";
import { makeRegisterOsobPage } from "./RegisterOsobPage";
import { makeRegisterPredmetovPage } from "./RegisterPredmetovPage";
import { makeZapisZPlanuPage, makeZapisZPonukyPage } from "./ZapisPage";
import { ZoznamPrihlasenychNaTerminModal } from "./ZoznamPrihlasenychNaTermin";
import { ModalBase, PageLayout } from "./layout";
import { navigate, QueryContext } from "./router";

function makeNotFoundPage() {
  return (
    <PageLayout>
      <p>Action not found!</p>
    </PageLayout>
  );
}

var actions: Record<string, () => React.ReactNode> = {
  index: makeIndexPage,
  priebezneHodnotenia: makePriebezneHodnoteniaPage,
  mojeHodnotenia: makeMojeHodnoteniaPage,
  mojePredmety: makeMojePredmetyPage,
  mojeSkusky: makeMojeSkuskyPage,
  prehladStudia: makePrehladStudiaPage,
  registerOsob: makeRegisterOsobPage,
  registerPredmetov: makeRegisterPredmetovPage,
  zapisZPlanu: makeZapisZPlanuPage,
  zapisZPonuky: makeZapisZPonukyPage,
};

var modalActions: Record<string, React.ComponentType> = {
  about: AboutModal,
  detailPredmetu: DetailPredmetuModal,
  zoznamPrihlasenychNaTermin: ZoznamPrihlasenychNaTerminModal,
};

export function App() {
  var query = useContext(QueryContext);
  var action = query.action || "index";
  var maker = actions[action] || makeNotFoundPage;
  var modalComponent = Votr.ajaxError
    ? ErrorModal
    : query.modal
    ? modalActions[query.modal]
    : undefined;

  function handleClose() {
    if (Votr.ajaxError) return;
    navigate(_.omitBy(query, (value, key) => key.substring(0, 5) == "modal"));
  }

  return (
    <React.Fragment>
      {maker()}
      <ModalBase component={modalComponent} onClose={handleClose} />
      <LogViewer />
    </React.Fragment>
  );
}
