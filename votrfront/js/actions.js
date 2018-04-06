
import { AboutModal, IndexPage } from './About';
import { DetailPredmetuModal } from './DetailPredmetu';
import { ErrorModal } from './ErrorPage';
import { LogViewer } from './LogViewer';
import { MojeHodnoteniaPage } from './MojeHodnoteniaPage';
import { PriebezneHodnoteniaPage } from './PriebezneHodnoteniaPage';
import { MojePredmetyPage } from './MojePredmetyPage';
import { MojeSkuskyPage } from './MojeSkuskyPage';
import { PrehladStudiaPage } from './PrehladStudiaPage';
import { RegisterOsobPage } from './RegisterOsobPage';
import { RegisterPredmetovPage } from './RegisterPredmetovPage';
import { ZapisZPlanuPage, ZapisZPonukyPage } from './ZapisPage';
import { ZoznamPrihlasenychNaTerminModal } from './ZoznamPrihlasenychNaTermin';
import { ModalBase, PageLayout } from './layout';
import { navigate, queryConsumer } from './router';
import { AnketaPopup } from './AnketaPopup';


export function NotFoundPage() {
  return (
    <PageLayout>
      <p>Action not found!</p>
    </PageLayout>
  );
}


export var actions = {
  index: IndexPage,
  priebezneHodnotenia: PriebezneHodnoteniaPage,
  mojeHodnotenia: MojeHodnoteniaPage,
  mojePredmety: MojePredmetyPage,
  mojeSkusky: MojeSkuskyPage,
  prehladStudia: PrehladStudiaPage,
  registerOsob: RegisterOsobPage,
  registerPredmetov: RegisterPredmetovPage,
  zapisZPlanu: ZapisZPlanuPage,
  zapisZPonuky: ZapisZPonukyPage
};


export var modalActions = {
  about: AboutModal,
  detailPredmetu: DetailPredmetuModal,
  zoznamPrihlasenychNaTermin: ZoznamPrihlasenychNaTerminModal
};


export function App() {
  return queryConsumer(query => {
    var action = query.action || 'index';
    var mainComponent = actions[action] || NotFoundPage;
    var modalComponent = Votr.ajaxError ? ErrorModal : modalActions[query.modal];

    function handleClose() {
      if (Votr.ajaxError) return;
      navigate(_.omit(query, (value, key) => key.substring(0, 5) == 'modal'));
    }

    var C = mainComponent;
    return <React.Fragment>
      <C />
      <ModalBase component={modalComponent} onClose={handleClose} />
      <LogViewer />
      <AnketaPopup />
    </React.Fragment>;
  });
}
