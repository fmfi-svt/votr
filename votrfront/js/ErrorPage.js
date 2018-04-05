
import { goLogout, goReset, goResetHome } from './ajax';
import { Modal, ModalBase } from './layout';
import { AnalyticsMixin, FakeLink } from './router';


export var ErrorModal = createReactClass({
  getInitialState() {
    return {
      open: false
    }
  },

  handleIgnore() {
    Votr.ajaxError = null;
    Votr.appRoot.forceUpdate();
  },

  handleDetails() {
    this.setState({ open: true });
  },

  render() {
    var error = Votr.settings.error || Votr.ajaxError;
    var lastLine = _.last(error.trim("\n").split("\n"));
    var type = lastLine.split(":")[0]

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
        description = "Votr nerozumie, čo spravil AIS. V novej verzii AISu sa asi niečo zmenilo.";
      }
      if (type == "aisikl.exceptions.AISBehaviorError") {
        if (lastLine.match(/args=\['(Nie je connection|Nastala SQL chyba)/)) {
          description = "AIS sa nevie pripojiť na svoju databázu.";
          contact = false;
        } else {
          description = "AIS spravil niečo nečakané a Votr si s tým nevie poradiť.";
        }
      }
    }

    // Some errors are caused by a malformed URL, so resetting won't help. If
    // we haven't navigated since the last full reload (the user has probably
    // reset just now), we redirect to the front page instead.
    var goHome = !Votr.didNavigate && !Votr.settings.error && location.search.substring(1);

    return <Modal title={title} closeButton={false}>
      <p className="text-center"><big>{description}</big></p>
      {contact &&
        <p className="text-center">
          Ak problém pretrváva, napíšte nám na <a
          href="mailto:fmfi-svt@googlegroups.com">fmfi-svt@googlegroups.com</a>.
        </p>}
      <br />
      <ul className="list-inline text-center">
        {goHome ?
          <li><button type="button" className="btn btn-primary"
                      onClick={goResetHome}>Späť na začiatok</button></li> :
          <li><button type="button" className="btn btn-primary"
                      onClick={goReset}>Skúsiť znova</button></li>}
        <li><button type="button" className="btn btn-default"
                    onClick={goLogout}>Odhlásiť</button></li>
      </ul>
      <br />
      {this.state.open ?
        <pre>{error}</pre> :
        <p className="text-center text-muted">
          Technické detaily: <code>{lastLine}</code>{" "}
          <FakeLink onClick={this.handleDetails}>Viac detailov...</FakeLink>
        </p>}
      {!Votr.settings.error && this.state.open &&
        <button type="button" className="btn btn-default"
                onClick={this.handleIgnore}>Ignorovať chybu</button>}
    </Modal>;
  }
});


export var ErrorPage = createReactClass({
  mixins: [AnalyticsMixin],

  render() {
    // TODO: ModalBase should probably use transferPropsTo() instead of requiring query.
    return <ModalBase query={{}} component={ErrorModal} onClose={_.noop} />
  }
});
