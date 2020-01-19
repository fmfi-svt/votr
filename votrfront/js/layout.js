
import PropTypes from 'prop-types';
import React from 'react';
import _ from 'lodash';
import $ from 'jquery';
import 'bootstrap-sass/assets/javascripts/bootstrap/transition';  // needed by modal.js.
import 'bootstrap-sass/assets/javascripts/bootstrap/modal';  // needed for $node.modal().
import { CacheRequester, Loading, goLogout, goReset, goResetHome, logs } from './ajax';
import { FakeLink, Link, queryConsumer } from './router';


export class ErrorBoundary extends React.Component {
  state = { error: undefined, open: false };

  componentDidCatch(error, errorInfo) {
    setTimeout(function () {
      console.error('ErrorBoundary caught error:', [error, errorInfo]);
      var body = {
        errorString: '' + error,
        stack: error && error.stack,
        componentStack: errorInfo.componentStack,
      };
      var xhr = new XMLHttpRequest();
      xhr.open("POST", "report?type=errorboundary", true);
      xhr.setRequestHeader("Content-Type", "application/json");
      xhr.send(JSON.stringify(body));
    }, 0);
  }

  static getDerivedStateFromError(error) {
    return { error: error };
  }

  handleDetails = () => {
    this.setState({ open: true });
  }

  render() {
    if (this.state.error) {
      var error = this.state.error.stack;
      var details = String(error && error.stack || error);
      var firstLine = details.trim("\n").split("\n")[0];
      return (
        <div className="alert alert-danger">
          <h3>Chyba</h3>
          <p>Vyskytla sa chyba a túto stránku nebolo možné zobraziť.</p>
          <p>
            Ak problém pretrváva, napíšte nám na <a
            href="mailto:fmfi-svt@googlegroups.com">fmfi-svt@googlegroups.com</a>.
          </p>
          <br />
          <ul className="list-inline">
            <li><button type="button" className="btn btn-primary"
                        onClick={goResetHome}>Späť na začiatok</button></li>
            <li><button type="button" className="btn btn-default"
                        onClick={goLogout}>Odhlásiť</button></li>
          </ul>
          <br />
          {this.state.open ?
            <pre>{details}</pre> :
            <p className="text-muted">
              Technické detaily: <code>{firstLine}</code>{" "}
              <FakeLink onClick={this.handleDetails}>Viac detailov...</FakeLink>
            </p>}
        </div>
      );
    } else {
      return this.props.children;
    }
  }
};


export function PageLayout(props) {
  return (
    <React.Fragment>
      <PageNavbar />
      <div className="layout-container">
        <div className="layout-menu">
          <MainMenu />
        </div>
        <div className="layout-content">
          <div className="container-fluid">
            <ErrorBoundary>
              {props.children}
            </ErrorBoundary>
          </div>
        </div>
      </div>
    </React.Fragment>
  );
}


export function PageNavbar() {
  return queryConsumer(query => (
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
            <li><Link href={{ ...query, modal: 'about' }}>O aplikácii</Link></li>
            <li><FakeLink onClick={goReset} title="Znovu načítať všetky dáta">Obnoviť</FakeLink></li>
            <li><FakeLink onClick={goLogout}>Odhlásiť</FakeLink></li>
          </ul>
        </div>
      </div>
    </div>
  ));
}


export function LogStatus() {
  var entry = _.last(logs);
  var message;
  if (!entry) {
    message = "\xA0"; // nbsp
  } else if (entry.log == 'http' && entry.message.match(/^Requesting/)) {
    message = "Čakám na AIS...";
  } else if (entry.log == 'rpc' && entry.message.match(/finished$/)) {
    message = "\xA0"; // nbsp
  } else {
    message = "Spracovávam dáta... (" + entry.message + ")";
  }
  return <p className="navbar-text">{message}</p>;
}


export class PageTitle extends React.Component {
  titleRef = React.createRef()

  componentDidMount() {
    document.title = this.titleRef.current.textContent;
  }

  componentDidUpdate() {
    document.title = this.titleRef.current.textContent;
  }

  render() {
    return <h1 ref={this.titleRef}>{this.props.children}</h1>;
  }
}


function MenuItem(props) {
  return queryConsumer(query => {
    var isActive = props.active || props.href.action == query.action;
    return (
      <li className={isActive ? 'active' : null}>
        <Link href={props.href}>{props.label}</Link>
      </li>
    );
  });
}


function DisabledItem(props) {
  // return <li className="disabled"><a>{props.label}</a></li>;
  return null;
}


export function MainMenu() {
  return queryConsumer(query => {
    var { action, studiumKey, zapisnyListKey } = query;

    var cache = new CacheRequester();
    var somStudent = cache.get('get_som_student');

    return (
      <ul className="main-menu nav nav-pills nav-stacked">
        <li><strong className="text-pill">Moje štúdium</strong></li>
        {somStudent === false && <li><span className="text-pill">Nie ste študentom.</span></li>}
        {somStudent && (
          <React.Fragment>
            <MenuItem label="Moje predmety" href={{ action: 'mojePredmety', zapisnyListKey }} />
            <MenuItem label="Moje skúšky" href={{ action: 'mojeSkusky', zapisnyListKey }} />
            <MenuItem label="Moje hodnotenia" href={{ action: 'mojeHodnotenia', studiumKey }} />
            <MenuItem label="Priebežné hodnotenia" href={{ action: 'priebezneHodnotenia', zapisnyListKey }} />
            <DisabledItem label="Môj rozvrh" />
            <MenuItem label="Zápis predmetov" href={{ action: 'zapisZPlanu', zapisnyListKey }} active={action == 'zapisZPonuky'} />
            <MenuItem label="Prehľad štúdia" href={{ action: 'prehladStudia' }} />
          </React.Fragment>
        )}
        {!cache.loadedAll && <li><span className="text-pill"><Loading requests={cache.missing} /></span></li>}
        <li><hr/></li>
        <li><strong className="text-pill">Registre</strong></li>
        <MenuItem label="Register osôb" href={{ action: 'registerOsob' }} />
        <MenuItem label="Register predmetov" href={{ action: 'registerPredmetov' }} />
        <DisabledItem label="Register miestností" />
        <DisabledItem label="Register študijných programov" />
      </ul>
    );
  });
}


export function FormItem(props) {
  if (props.label) {
    return (
      <label className="form-item">
        <div className="col-sm-4 form-item-label">{props.label}</div>
        <div className="col-sm-8">{props.children}</div>
      </label>
    );
  } else {
    return (
      <div className="form-item">
        <div className="col-sm-offset-4 col-sm-8">{props.children}</div>
      </div>
    );
  }
}


export class ModalBase extends React.Component {
  static propTypes = {
    component: PropTypes.func,
    onClose: PropTypes.func.isRequired,
  };

  modalRef = React.createRef()

  componentDidMount() {
    var $node = $(this.modalRef.current);
    $node.modal();
    $node.on('hide.bs.modal', (e) => {
      if ($node.attr('data-show') == 'true') {
        e.preventDefault();
        this.props.onClose();
      }
    });
  }

  componentDidUpdate() {
    var $node = $(this.modalRef.current);
    $node.modal($node.attr('data-show') == 'true' ? 'show' : 'hide');
  }

  render() {
    var C = this.props.component;

    return <div data-show={Boolean(C)} className="modal fade" ref={this.modalRef}
                tabIndex="-1" role="dialog" aria-hidden="true">
      <div className="modal-dialog modal-lg">
        {C && (
          <ErrorBoundary>
            <C />
          </ErrorBoundary>
        )}
      </div>
    </div>;
  }
}


export function Modal(props) {
  return (
    <div className="modal-content">
      <div className="modal-header">
        {props.closeButton &&
          <button type="button" className="close" data-dismiss="modal">
            <span aria-hidden="true">&times;</span>
            <span className="sr-only">Close</span>
          </button>}
        <h4 className="modal-title">{props.title}</h4>
      </div>
      <div className="modal-body">
        <ErrorBoundary>
          {props.children}
        </ErrorBoundary>
      </div>
      {props.footer}
    </div>
  );
}

Modal.propTypes = {
  closeButton: PropTypes.bool.isRequired,
  title: PropTypes.node.isRequired,
  footer: PropTypes.node
};

Modal.defaultProps = {
  closeButton: true
};
