/** @jsx React.DOM */

(function () {


Votr.PageLayout = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  render: function () {
    return <div className="page">
      <h1>Votr</h1>
      {_.last(Votr.logs, 5).map((entry, index) =>
        <div key={index}><code>[{entry.log}] {entry.message}</code></div>
      )}
      <Votr.MainMenu query={this.props.query} />
      <div className="content">
        {this.props.children}
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
    return <li>
      <Votr.Link href={href} className={isActive ? 'active' : null}>
        {content}
      </Votr.Link>
    </li>;
  },

  render: function () {
    var {studiumKey, zapisnyListKey} = this.props.query;

    return <ul className="main-menu">
      <li><strong>Moje štúdium</strong></li>
      <li><del>Prehľad štúdia</del></li>
      {this.renderMenuItem("Moje predmety", { action: 'mojePredmety', studiumKey, zapisnyListKey })}
      {this.renderMenuItem("Moje skúšky", { action: 'mojeSkusky', studiumKey, zapisnyListKey })}
      {this.renderMenuItem("Moje hodnotenia", { action: 'mojeHodnotenia', studiumKey })}
      <li><del>Môj rozvrh</del></li>
      <li><strong>Register</strong></li>
      <li><del>Register osôb</del></li>
      {this.renderMenuItem("Register predmetov", { action: 'registerPredmetov' })}
      <li><del>Register miestností</del></li>
      <li><del>Register študijných programov</del></li>
    </ul>;
  }
});


})();
