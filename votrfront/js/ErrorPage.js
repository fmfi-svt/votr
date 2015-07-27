
import { goLogout, goReset, goResetHome } from './ajax';
import { Modal, ModalBase } from './layout';
import { AnalyticsMixin, FakeLink } from './router';


export var ErrorModal = React.createClass({
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

    // TODO: Lepsie chybove hlasky. Napisat ze sme to zalogovali a vyriesime, a
    // ze co maju robit (zavolat CEPITu / pisat nam / skusit to cez AIS / ...).
    var title = "Chyba";
    var description = "Vyskytla sa chyba a vaša požiadavka nebola spracovaná.";

    if (Votr.settings.error) {
      if (type == "aisikl.exceptions.LoggedOutError") {
        title = "Prihlásenie vypršalo";
        description = "Vaše prihlásenie vypršalo. Skúste znova.";
      } else {
        title = "Chyba pripojenia";
        description = "Votr sa nevie pripojiť na AIS.";
      }
    } else {
      if (type == "aisikl.exceptions.AISParseError") {
        description = "Votr nerozumie, čo spravil AIS. V novej verzii AISu sa asi niečo zmenilo.";
      }
      if (type == "aisikl.exceptions.AISBehaviorError") {
        description = "AIS spravil niečo nečakané. V novej verzii AISu sa možno niečo zmenilo.";
      }
    }

    // Some errors are caused by a malformed URL, so resetting won't help. If
    // we haven't navigated since the last full reload (the user has probably
    // reset just now), we redirect to the front page instead.
    var goHome = !Votr.didNavigate && !Votr.settings.error && location.search.substring(1);

    // TODO: Restyle buttons to make them look less like bootstrap.
    return <Modal title={title} closeButton={false}>
      <p className="text-center"><big>{description}</big></p>
      <ul className="list-inline text-center">
        {goHome ?
          <li><button type="button" className="btn btn-primary"
                      onClick={goResetHome}>Späť na začiatok</button></li> :
          <li><button type="button" className="btn btn-primary"
                      onClick={goReset}>Skúsiť znova</button></li>}
        <li><button type="button" className="btn btn-default"
                    onClick={goLogout}>Odhlásiť</button></li>
      </ul>
      <br /><br />
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


export var ErrorPage = React.createClass({
  mixins: [AnalyticsMixin],

  render() {
    // TODO: ModalBase should probably use transferPropsTo() instead of requiring query.
    return <ModalBase query={{}} component={ErrorModal} onClose={_.noop} />
  }
});
