/** @jsx React.DOM */

(function () {


Votr.PageLayout = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  render: function () {
    return <div>
      <Votr.PageNavbar />
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
        </div>
        <div className="navbar-right">
        </div>
      </div>
    </div>;
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

  renderMenuItem: function (content, href) {
    var isActive = href.action == this.props.query.action;
    return <li className={isActive ? 'active' : null}>
      <Votr.Link href={href}>{content}</Votr.Link>
    </li>;
  },

  renderDisabled: function (content) {
    return <li className="disabled"><a>{content}</a></li>;
  },

  render: function () {
    var {studiumKey, zapisnyListKey} = this.props.query;

    return <ul className="main-menu nav nav-pills nav-stacked">
      <li><strong className="text-pill">Moje štúdium</strong></li>
      {this.renderDisabled("Prehľad štúdia")}
      {this.renderMenuItem("Moje predmety", { action: 'mojePredmety', studiumKey, zapisnyListKey })}
      {this.renderMenuItem("Moje skúšky", { action: 'mojeSkusky', studiumKey, zapisnyListKey })}
      {this.renderMenuItem("Moje hodnotenia", { action: 'mojeHodnotenia', studiumKey })}
      {this.renderDisabled("Môj rozvrh")}
      <li><hr/></li>
      <li><strong className="text-pill">Register</strong></li>
      {this.renderDisabled("Register osôb")}
      {this.renderDisabled("Register predmetov")}
      {this.renderDisabled("Register miestností")}
      {this.renderDisabled("Register študijných programov")}
    </ul>;
  }
});


})();
