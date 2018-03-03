import React, { Component } from 'react';
import PropTypes from 'prop-types';

import { ZapisnyListSelector } from './ZapisnyListSelector';
import { CacheRequester, Loading } from './ajax';
import { PageLayout, PageTitle } from './layout';
import { Link } from './router';
import { humanizeBoolean } from './humanizeAISData';

export class PriebezneHodnoteniaPageContent extends Component {

  renderContent = () => {
    const cache = new CacheRequester();
    const { zapisnyListKey } = this.props.query;
    let [priebezneHodnotenia, message] = cache.get('get_priebezne_hodnotenia', zapisnyListKey) || [];

    if (!priebezneHodnotenia) {
      return <Loading requests={cache.missing} />;
    }

    if (!message && !priebezneHodnotenia.length) {
      message = 'Tento zápisný list nemá žiadne priebežné hodnotenia.';
    }

    return (
      <div>
        {priebezneHodnotenia.map((priebHod, key) => (
          <div key={key}>
            <h2>
              <Link href={{
                ...this.props.query,
                modal: 'detailPredmetu',
                modalPredmetKey: priebHod.predmet_key,
                modalAkademickyRok: priebHod.akademicky_rok,
              }}>
                {priebHod.nazov}
              </Link>
            </h2>
            <table className="table table-condensed table-bordered table-striped table-hover">
              <thead>
                <tr>
                  <th>Popis</th>
                  <th>Body</th>
                  <th>Zaevidoval</th>
                  <th>Započítavať</th>
                  <th>Minimum</th>
                </tr>
              </thead>
              <tbody>
                {priebHod.zaznamy.map((zaznam, key) => (
                  <tr key={key}>
                    <td>{zaznam.dovod}</td>
                    <td>{zaznam.poc_bodov} / {zaznam.maximum}</td>
                    <td>{zaznam.zaevidoval}</td>
                    <td>{humanizeBoolean(zaznam.zapocitavat)}</td>
                    <td>{zaznam.minimum}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
        {message && <strong>{message}</strong>}
      </div>
    );
  }

  render() {
    return (
      <div>
        <div className="header">
          <PageTitle>Priebežné hodnotenia</PageTitle>
        </div>
        {this.renderContent()}
      </div>
    );
  }
}

PriebezneHodnoteniaPageContent.propTypes = {
  query: PropTypes.object.isRequired,
};

export class PriebezneHodnoteniaPage extends Component {
  render() {
    return (
      <PageLayout query={this.props.query}>
        <ZapisnyListSelector
          query={this.props.query}
          component={PriebezneHodnoteniaPageContent}
        />
      </PageLayout>
    );
  }
}

PriebezneHodnoteniaPage.propTypes = {
  query: PropTypes.object.isRequired,
};
