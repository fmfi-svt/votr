import React, { Component } from 'react';
import PropTypes from 'prop-types';
import $ from 'jquery';

import { CacheRequester, Loading, goLogout, goReset, logs } from './ajax';
import { FakeLink, Link } from './router';

export class PageLayout extends Component {
  render() {
    return (
      <div>
        <PageNavbar query={this.props.query} />
        <div className="layout-container">
          <div className="layout-menu">
            <MainMenu query={this.props.query} />
          </div>
          <div className="layout-content">
            <div className="container-fluid">
              {this.props.children}
            </div>
          </div>
        </div>
      </div>
    );
  }
}

PageLayout.propTypes = {
  query: PropTypes.object.isRequired,
};

export class PageNavbar extends Component {
  render() {
    return (
      <div className="navbar navbar-inverse navbar-static-top">
        <div className="container-fluid">
          <div className="navbar-header">
            <Link className="navbar-brand" href={{}}>Votr</Link>
          </div>
          <div className="navbar-left">
            <LogStatus />
          </div>
          <div className="navbar-right">
            <ul className="nav navbar-nav">
              <li><Link href={{ ...this.props.query, modal: 'about' }}>O aplikácii</Link></li>
              <li><FakeLink onClick={goReset} title="Znovu načítať všetky dáta">Obnoviť</FakeLink></li>
              <li><FakeLink onClick={goLogout}>Odhlásiť</FakeLink></li>
            </ul>
          </div>
        </div>
      </div>
    );
  }
}

export class LogStatus extends Component {
  render() {
    const entry = logs[logs.length - 1];
    let message;
    if (!entry) {
      message = '\xA0'; // nbsp
    } else if (entry.log === 'http' && entry.message.match(/^Requesting/)) {
      message = 'Čakám na AIS...';
    } else if (entry.log === 'rpc' && entry.message.match(/finished$/)) {
      message = '\xA0'; // nbsp
    } else {
      message = `Spracovávam dáta... (${entry.message}")`;
    }
    return (
      <p className="navbar-text">
        {message}
      </p>
    );
  }
}

export class PageTitle extends Component {
  componentDidMount() {
    document.title = this.refs.title.textContent;
  }

  componentDidUpdate() {
    document.title = this.refs.title.textContent;
  }

  render() {
    return <h1 ref="title">{this.props.children}</h1>;
  }
}

export class MainMenu extends Component {

  renderMenuItem(content, href, moreActions) {
    const isActive = href.action === this.props.query.action
      || (moreActions && moreActions[this.props.query.action]);
    return (
      <li className={isActive ? 'active' : null}>
        <Link href={href}>{content}</Link>
      </li>
    );
  }

  renderDisabled(content) {
    return <li className="disabled"><a>{content}</a></li>;
  }

  render() {
    const { studiumKey, zapisnyListKey } = this.props.query;

    const cache = new CacheRequester();
    const somStudent = cache.get('get_som_student');

    return (
      <ul className="main-menu nav nav-pills nav-stacked">
        <li><strong className="text-pill">Moje štúdium</strong></li>

        {!somStudent && (<li><span className="text-pill">Nie ste študentom.</span></li>)}
        {somStudent && this.renderMenuItem('Moje predmety', { action: 'mojePredmety', zapisnyListKey })}
        {somStudent && this.renderMenuItem('Moje skúšky', { action: 'mojeSkusky', zapisnyListKey })}
        {somStudent && this.renderMenuItem('Moje hodnotenia', { action: 'mojeHodnotenia', studiumKey })}
        {somStudent && this.renderMenuItem(
          'Priebežné hodnotenia',
          { action: 'priebezneHodnotenia', zapisnyListKey }
        )}
        {/*somStudent && this.renderDisabled('Môj rozvrh')*/}
        {somStudent && this.renderMenuItem(
          'Zápis predmetov',
          { action: 'zapisZPlanu', zapisnyListKey }, { zapisZPonuky: true }
        )}
        {somStudent && this.renderMenuItem('Prehľad štúdia', { action: 'prehladStudia' })}
        {!cache.loadedAll && (<li><span className="text-pill"><Loading requests={cache.missing} /></span></li>)}
        <li><hr /></li>
        <li><strong className="text-pill">Registre</strong></li>
        {this.renderMenuItem('Register osôb', { action: 'registerOsob' })}
        {this.renderMenuItem('Register predmetov', { action: 'registerPredmetov' })}
        {/*this.renderDisabled('Register miestností')*/}
        {/*this.renderDisabled('Register študijných programov')*/}
      </ul>
    );
  }
};

MainMenu.propTypes = {
  query: PropTypes.object.isRequired,
};

export class FormItem extends Component {
  render() {
    if (this.props.label) {
      return (
        <label className="form-item">
          <div className="col-sm-4 form-item-label">{this.props.label}</div>
          <div className="col-sm-8">{this.props.children}</div>
        </label>
      );
    } else {
      return (
        <div className="form-item">
          <div className="col-sm-offset-4 col-sm-8">{this.props.children}</div>
        </div>
      );
    }
  }
}

export class ModalBase extends Component {

  componentDidMount() {
    const $node = $(this.refs.modal);
    $node.modal();
    $node.on('hide.bs.modal', (e) => {
      if ($node.attr('data-show') === 'true') {
        e.preventDefault();
        this.props.onClose();
      }
    });
  }

  componentDidUpdate() {
    const $node = $(this.refs.modal);
    $node.modal($node.attr('data-show') === 'true' ? 'show' : 'hide');
  }

  render() {
    const C = this.props.component;

    return (
      <div
        data-show={Boolean(C)}
        className="modal fade"
        ref="modal"
        tabIndex="-1"
        role="dialog"
        aria-hidden="true"
      >
        <div className="modal-dialog modal-lg">
          {C && <C query={this.props.query} />}
        </div>
      </div>
    );
  }
}

ModalBase.propTypes = {
  component: PropTypes.func,
  onClose: PropTypes.func.isRequired,
  query: PropTypes.object.isRequired,
};

// TODO Refactor all modals to use something like react-bootstrap
// so that the files in libs/ are not required

export class Modal extends Component {

  render() {
    return (
      <div className="modal-content">
        <div className="modal-header">
          {this.props.closeButton &&
            <button type="button" className="close" data-dismiss="modal">
              <span aria-hidden="true">&times;</span>
              <span className="sr-only">Close</span>
            </button>}
          <h4 className="modal-title">{this.props.title}</h4>
        </div>
        <div className="modal-body">
          {this.props.children}
        </div>
        {this.props.footer}
      </div>
    );
  }
}

Modal.propTypes = {
  closeButton: PropTypes.bool.isRequired,
  title: PropTypes.node.isRequired,
  footer: PropTypes.node,
};

Modal.defaultProps = {
  closeButton: true,
};
