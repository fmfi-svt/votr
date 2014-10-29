/** @jsx React.DOM */

(function () {


var TYPE_NAMES = {
  'cosignproxy': 'Cosign (automatické)',
  'cosignpassword': 'Cosign (meno a heslo)',
  'cosigncookie': 'Cosign (manuálne cookie)',
  'plainpassword': 'Meno a heslo',
  'demo': 'Demo'
};


Votr.LoginForm = React.createClass({
  getInitialState: function () {
    return {
      server: Votr.settings.server || 0,
      type: Votr.settings.type
    };
  },

  handleServerChange: function (event) {
    this.replaceState({ server: event.target.value });
  },

  handleTypeChange: function (event) {
    this.replaceState({ server: this.state.server, type: event.target.value });
  },

  handleFieldChange: function (event) {
    var update = {};
    update[event.target.name] = event.target.value;
    this.setState(update)
  },

  render: function () {
    var serverConfig = Votr.settings.servers[this.state.server];
    var currentType = this.state.type || serverConfig.login_types[0];

    return <form className="login" action="login" method="POST">
      {Votr.settings.invalid_session &&
        <p className="error">Vaše prihlásenie vypršalo. Prihláste sa znova.</p>}

      {Votr.settings.error &&
        <div>
          <p className="error">Prihlásenie sa nepodarilo.</p>
          <pre>{Votr.settings.error}</pre>
          {/* TODO: Hide the full exception behind a "Show details" link. */}
        </div>}

      <input type="hidden" name="destination" value={location.search} />

      {Votr.settings.servers.length > 1 ?
        <p>
          <label>
            {"Server: "}
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
            {"Typ prihlásenia: "}
            <select name="type" value={currentType} onChange={this.handleTypeChange}>
              {serverConfig.login_types.map((type) =>
                <option key={type} value={type}>{TYPE_NAMES[type]}</option>
              )}
            </select>
          </label>
        </p> :
        <input type="hidden" name="type" value={currentType} />
      }

      {(currentType == 'cosignpassword' || currentType == 'plainpassword') &&
        <div>
          <p>
            <label>
              {"Meno: "}
              <input name="username" value={this.state.username}
                     onChange={this.handleFieldChange} />
            </label>
          </p>
          <p>
            <label>
              {"Heslo: "}
              <input name="password" value={this.state.password}
                     onChange={this.handleFieldChange} type="password" />
            </label>
          </p>
        </div>}

      {currentType == 'cosigncookie' &&
        <div>
          {/* TODO: Detailed instructions for cosigncookie. */}
          <p>
            <label>
              {"Hodnota cookie " + serverConfig.ais_cookie + ": "}
              <input name="cookie" value={this.state.cookie}
                     onChange={this.handleFieldChange} />
            </label>
          </p>
        </div>}

      <button type="submit" className="btn btn-lg btn-primary center-block">Prihlásiť</button>
    </form>;
  }
});


Votr.LoginPage = React.createClass({
  render: function () {
    return <div>
      <div className="navbar navbar-inverse navbar-static-top">
        <div className="container-fluid">
          <div className="navbar-header">
            <a href={Votr.settings.url_root} className="navbar-brand">Votr</a>
          </div>
        </div>
      </div>
      <div className="login-page">
        <p>
          <strong>Votr</strong> ponúka študentom jednoduchší a pohodlnejší
          spôsob, ako robiť najčastejšie činnosti zo systému AIS. Zapíšte sa na
          skúšky, prezrite si vaše hodnotenia a skontrolujte si počet kreditov
          bez zbytočného klikania.
        </p>
        <hr />
        <Votr.LoginForm />
      </div>
    </div>;
  }
});


})();
