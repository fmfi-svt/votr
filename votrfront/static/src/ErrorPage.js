/** @jsx React.DOM */

(function () {


Votr.ErrorModal = React.createClass({
  getInitialState: function () {
    return {
      open: false
    }
  },

  handleIgnore: function () {
    Votr.ajaxError = null;
    Votr.appRoot.forceUpdate();
  },

  handleDetails: function () {
    this.setState({ open: true });
  },

  render: function () {
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

    // TODO: Restyle buttons to make them look less like bootstrap.
    return <Votr.Modal title={title} closeButton={false}>
      <p className="text-center"><big>{description}</big></p>
      <ul className="list-inline text-center">
        <li><button type="button" className="btn btn-primary"
                    onClick={Votr.goReset}>Skúsiť znova</button></li>
        <li><button type="button" className="btn btn-default"
                    onClick={Votr.goLogout}>Odhlásiť</button></li>
      </ul>
      <br /><br />
      {this.state.open ?
        <pre>{error}</pre> :
        <p className="text-center text-muted">
          Technické detaily: <code>{lastLine}</code>{" "}
          <Votr.FakeLink onClick={this.handleDetails}>Viac detailov...</Votr.FakeLink>
        </p>}
      {!Votr.settings.error && this.state.open &&
        <button type="button" className="btn btn-default"
                onClick={this.handleIgnore}>Ignorovať chybu</button>}
    </Votr.Modal>;
  }
});


Votr.ErrorPage = React.createClass({
  render: function () {
    // TODO: ModalBase should probably use transferPropsTo() instead of requiring query.
    return <Votr.ModalBase query={{}} component={Votr.ErrorModal} onClose={_.noop} />
  }
});


})();
