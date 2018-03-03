import React, { Component } from 'react';

import { AboutModal } from './About';
import { Modal, ModalBase } from './layout';
import { AnalyticsMixin, FakeLink } from './router';

const TYPE_NAMES = {
  cosignproxy: 'Cosign (automatické)',
  cosignpassword: 'Cosign (meno a heslo)',
  cosigncookie: 'Cosign (manuálne cookie)',
  plainpassword: 'Meno a heslo',
  demo: 'Demo',
};

export class LoginForm extends Component {
  componentWillMount() {
    this.setState({
      server: Votr.settings.server || 0,
      type: Votr.settings.type,
    });
  }

  handleServerChange = (event) => {
    const server = event.target.value;
    const newTypes = Votr.settings.servers[server].login_types;
    const type = newTypes.indexOf(this.state.type) > -1 ? this.state.type : null;
    this.setState({ server, type });
  }

  handleTypeChange = (event) => {
    this.setState({ type: event.target.value });
  }

  render() {
    const serverConfig = Votr.settings.servers[this.state.server];
    const currentType = this.state.type || serverConfig.login_types[0];
    let error;
    if (Votr.settings.error) {
      const errors = Votr.settings.error.trim('\n').split('\n');
      error = errors[errors.length - 1];
    }
    return (
      <form className="login" action="login" method="POST">
        {Votr.settings.invalid_session &&
          <p>Vaše prihlásenie vypršalo. Prihláste sa znova.</p>}

        {error && (
          <div>
            <p>Prihlásenie sa nepodarilo.</p>
            <p>
              {'Technické detaily: '}
              <code className="login-error">
                {error}
              </code>
              {' '}
              <FakeLink onClick={this.props.onOpenError}>Viac detailov...</FakeLink>
            </p>
            <p>
              Ak problém pretrváva, napíšte nám na
              <a className="text-nowrap" href="mailto:fmfi-svt@googlegroups.com">
                fmfi-svt@googlegroups.com
              </a>.
            </p>
            <hr />
          </div>
        )}

        <input type="hidden" name="destination" value={location.search} />

        {Votr.settings.servers.length > 1 ?
          <p>
            <label>
              {'Server: '}
              <select name="server" value={this.state.server} onChange={this.handleServerChange}>
                {Votr.settings.servers.map((server, index) =>
                  <option key={index} value={index}>{server.title}</option>
                )}
              </select>
            </label>
          </p> :
          <input type="hidden" name="server" value="0" />
        }

        {serverConfig.login_types.length > 1 ?
          <p>
            <label>
              {'Typ prihlásenia: '}
              <select name="type" value={currentType} onChange={this.handleTypeChange}>
                {serverConfig.login_types.map((type) =>
                  <option key={type} value={type}>{TYPE_NAMES[type]}</option>
                )}
              </select>
            </label>
          </p> :
          <input type="hidden" name="type" value={currentType} />
        }

        {(currentType === 'cosignpassword' || currentType === 'plainpassword') &&
          <div>
            <p>
              <label>
                {'Meno: '}
                <input name="username" />
              </label>
            </p>
            <p>
              <label>
                {'Heslo: '}
                <input name="password" type="password" />
              </label>
            </p>
          </div>}

        {currentType === 'cosigncookie' &&
          <div>
            {/* TODO: Detailed instructions for cosigncookie. */}
            {serverConfig.ais_cookie &&
              <p>
                <label>
                  {`Hodnota cookie ${serverConfig.ais_cookie}: `}
                  <input name="ais_cookie" />
                </label>
              </p>}
            {serverConfig.rest_cookie &&
              <p>
                <label>
                  {`Hodnota cookie ${serverConfig.rest_cookie}: `}
                  <input name="rest_cookie" />
                </label>
              </p>}
          </div>}

        <button type="submit" className="btn btn-lg btn-primary center-block">Prihlásiť</button>
      </form>
    );
  }
}

export class LoginErrorModal extends Component {
  render() {
    return (
      <Modal title="Chyba pri prihlásení">
        <pre>{Votr.settings.error}</pre>
      </Modal>
    );
  }
}

export class LoginPage extends Component {

  componentWillMount() {
    this.setState({ modal: null });
  }

  openAbout = () => {
    this.setState({ modal: 'about' });
  }

  openError = () => {
    this.setState({ modal: 'error' });
  }

  closeModal = () => {
    this.setState({ modal: null });
  }

  render() {
    const content = (
      <div className="login-page">
        <div className="navbar navbar-inverse navbar-static-top">
          <div className="container-fluid">
            <div className="navbar-header">
              <a href={Votr.settings.url_root} className="navbar-brand">Votr</a>
            </div>
          </div>
        </div>
        <div className="login-content">
          <p>
            <strong>Votr</strong> ponúka študentom jednoduchší a pohodlnejší
            spôsob, ako robiť najčastejšie činnosti zo systému AIS. Zapíšte sa na
            skúšky, prezrite si vaše hodnotenia a skontrolujte si počet kreditov
            bez zbytočného klikania.
          </p>
          <hr />
          <LoginForm onOpenError={this.openError} />
        </div>
        <div className="text-center">
          <ul className="list-inline">
            <li><FakeLink className="btn btn-link" onClick={this.openAbout}>O aplikácii</FakeLink></li>
            <li><a className="btn btn-link" href="https://uniba.sk/" target="_blank">Univerzita Komenského</a></li>
            <li><a className="btn btn-link" href="https://moja.uniba.sk/" target="_blank">IT služby na UK</a></li>
          </ul>
        </div>
      </div>
    );

    const modals = { about: AboutModal, error: LoginErrorModal };
    const modalComponent = modals[this.state.modal];

    return (
      <span>
        {content}
        <ModalBase query={{}} component={modalComponent} onClose={this.closeModal} />
      </span>
    );
  }
}

LoginPage.mixins = [AnalyticsMixin];
