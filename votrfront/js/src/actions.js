import React, { Component } from 'react';
import PropTypes from 'prop-types';

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

export class NotFoundPage extends Component {
  render() {
    return (
      <PageLayout query={this.props.query}>
        <p>Action not found!</p>
      </PageLayout>
    );
  }
}

export const actions = {
  index: IndexPage,
  priebezneHodnotenia: PriebezneHodnoteniaPage,
  mojeHodnotenia: MojeHodnoteniaPage,
  mojePredmety: MojePredmetyPage,
  mojeSkusky: MojeSkuskyPage,
  prehladStudia: PrehladStudiaPage,
  registerOsob: RegisterOsobPage,
  registerPredmetov: RegisterPredmetovPage,
  zapisZPlanu: ZapisZPlanuPage,
  zapisZPonuky: ZapisZPonukyPage,
};

export const modalActions = {
  about: AboutModal,
  detailPredmetu: DetailPredmetuModal,
  zoznamPrihlasenychNaTermin: ZoznamPrihlasenychNaTerminModal,
};

export class App extends Component {

  handleModalClose = () => {
    if (Votr.ajaxError) return;
    // remove ?modal=xxxx from querystring
    const newQueryParams = Object
      .keys(this.props.query)
      .filter((key) => key.substring(0, 5) !== 'modal')
      .reduce(
        (newObj, key) => {
          newObj[key] = this.props.query[key];
          return newObj;
        },
        {}
      );

    navigate(newQueryParams);
  }

  render() {
    const query = this.props.query;
    const action = query.action || 'index';
    const mainComponent = actions[action] || NotFoundPage;
    const modalComponent = Votr.ajaxError ? ErrorModal : modalActions[query.modal];

    const C = mainComponent;

    return (
      <div>
        <C query={query} />
        <ModalBase
          query={query}
          component={modalComponent}
          onClose={this.handleModalClose}
        />
        <LogViewer />
        <AnketaPopup />
      </div>
    );
  }
}

App.propTypes = {
  query: PropTypes.object.isRequired,
};
