(function () {


Votr.PageLayout = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  render: function () {
    return <div>
      <Votr.PageNavbar query={this.props.query} />
      <div className="layout-container">
        <div className="layout-menu">
          <Votr.MainMenu query={this.props.query} />
        </div>
        <div className="layout-content">
          <div className="container-fluid">
            {this.props.children}
          </div>
        </div>
      </div>
    </div>;
  }
});


Votr.PageNavbar = React.createClass({
  render: function () {
    return <div className="navbar navbar-inverse navbar-static-top">
      <div className="container-fluid">
        <div className="navbar-header">
          <Votr.Link className="navbar-brand" href={{}}>Votr</Votr.Link>
        </div>
        <div className="navbar-left">
          <Votr.LogStatus />
        </div>
        <div className="navbar-right">
          <ul className="nav navbar-nav">
            <li><Votr.Link href={_.assign({}, this.props.query, { modal: 'about' })}>O aplikácii</Votr.Link></li>
            <li><Votr.FakeLink onClick={Votr.goReset} title="Znovu načítať všetky dáta">Obnoviť</Votr.FakeLink></li>
            <li><Votr.FakeLink onClick={Votr.goLogout}>Odhlásiť</Votr.FakeLink></li>
          </ul>
        </div>
      </div>
    </div>;
  }
});


Votr.LogStatus = React.createClass({
  render: function () {
    var entry = _.last(Votr.logs);
    if (!entry) {
      var message = "\xA0";
    } else {
      var message = "Spracovávam dáta... (" + entry.message + ")";
      if (entry.log == 'http' && entry.message.match(/^Requesting/)) {
        message = "Čakám na AIS...";
	    }
      if (entry.log == 'rpc' && entry.message.match(/finished$/)) {
        message = "\xA0";
      }
    }
    return <p className="navbar-text">{message}</p>;
  }
});


Votr.PageTitle = React.createClass({
  componentDidMount: function () {
    document.title = this.getDOMNode().textContent;
  },

  componentDidUpdate: function () {
    document.title = this.getDOMNode().textContent;
  },

  render: function () {
    return <h1>{this.props.children}</h1>;
  }
});


Votr.MainMenu = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  renderMenuItem: function (content, href, moreActions) {
    var isActive = href.action == this.props.query.action || (moreActions && moreActions[this.props.query.action]);
    return <li className={isActive ? 'active' : null}>
      <Votr.Link href={href}>{content}</Votr.Link>
    </li>;
  },

  renderDisabled: function (content) {
    return <li className="disabled"><a>{content}</a></li>;
  },

  render: function () {
    var {studiumKey, zapisnyListKey} = this.props.query;

    var cache = new Votr.CacheRequester();
    var somStudent = cache.get('get_som_student');

    return <ul className="main-menu nav nav-pills nav-stacked">
      <li><strong className="text-pill">Moje štúdium</strong></li>
      {somStudent === false && <li><span className="text-pill">Nie ste študentom.</span></li>}
      {somStudent && this.renderMenuItem("Moje predmety", { action: 'mojePredmety', zapisnyListKey })}
      {somStudent && this.renderMenuItem("Moje skúšky", { action: 'mojeSkusky', zapisnyListKey })}
      {somStudent && this.renderMenuItem("Moje hodnotenia", { action: 'mojeHodnotenia', studiumKey })}
      {/*somStudent && this.renderDisabled("Môj rozvrh")*/}
      {somStudent && this.renderMenuItem("Zápis predmetov", { action: 'zapisZPlanu', zapisnyListKey }, { zapisZPonuky: true })}
      {somStudent && this.renderMenuItem("Prehľad štúdia", { action: 'prehladStudia' })}
      {!cache.loadedAll && <li><span className="text-pill"><Votr.Loading requests={cache.missing} /></span></li>}
      <li><hr/></li>
      <li><strong className="text-pill">Registre</strong></li>
      {this.renderMenuItem("Register osôb", { action: 'registerOsob' })}
      {this.renderMenuItem("Register predmetov", { action: 'registerPredmetov' })}
      {/*this.renderDisabled("Register miestností")*/}
      {/*this.renderDisabled("Register študijných programov")*/}
    </ul>;
  }
});


Votr.FormItem = React.createClass({
  render: function () {
    if (this.props.label) {
      return <label className="form-item">
        <div className="col-sm-4 form-item-label">{this.props.label}</div>
        <div className="col-sm-8">{this.props.children}</div>
      </label>;
    } else {
      return <div className="form-item">
        <div className="col-sm-offset-4 col-sm-8">{this.props.children}</div>
      </div>;
    }
  }
});


Votr.ModalBase = React.createClass({
  propTypes: {
    component: React.PropTypes.func,
    onClose: React.PropTypes.func.isRequired,
    query: React.PropTypes.object.isRequired
  },

  componentDidMount: function () {
    var $node = $(this.getDOMNode());
    $node.modal();
    $node.on('hide.bs.modal', (e) => {
      if ($node.attr('data-show') == 'true') {
        e.preventDefault();
        this.props.onClose();
      }
    });
  },

  componentDidUpdate: function () {
    var $node = $(this.getDOMNode());
    $node.modal($node.attr('data-show') == 'true' ? 'show' : 'hide');
  },

  render: function () {
    var C = this.props.component;

    return <div data-show={Boolean(C)} className="modal fade"
                tabIndex="-1" role="dialog" aria-hidden="true">
      <div className="modal-dialog modal-lg">
        {C && <C query={this.props.query} />}
      </div>
    </div>;
  }
});


Votr.Modal = React.createClass({
  propTypes: {
    closeButton: React.PropTypes.bool.isRequired,
    title: React.PropTypes.node.isRequired,
    footer: React.PropTypes.node
  },

  getDefaultProps: function () {
    return {
      closeButton: true
    };
  },

  render: function () {
    return <div className="modal-content">
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
    </div>;
  }
});


})();
