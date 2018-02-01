
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
import { navigate } from './router';
import { AnketaPopup } from './AnketaPopup';


export var NotFoundPage = React.createClass({
  render() {
    return <PageLayout query={this.props.query}>
      <p>Action not found!</p>
    </PageLayout>;
  }
});


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


export var App = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  handleClose() {
    if (Votr.ajaxError) return;
    navigate(_.omit(
        this.props.query, (value, key) => key.substring(0, 5) == 'modal'));
  },

  render() {
    var query = this.props.query;
    var action = query.action || 'index';
    var mainComponent = actions[action] || NotFoundPage;
    var modalComponent = Votr.ajaxError ? ErrorModal : modalActions[query.modal];

    var C = mainComponent;
    return <div>
      <C query={query} />
      <ModalBase query={query} component={modalComponent} onClose={this.handleClose} />
      <LogViewer />
      <AnketaPopup />
    </div>;
  }
});
