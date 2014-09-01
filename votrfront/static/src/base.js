/**
 * @jsx React.DOM
 * @require react.min.js
 */

(function () {


Votr.t = function (str) {
  return str;
}


Votr.PageLayout = React.createClass({
  render: function () {
    return <div>{this.props.children}</div>;
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


})();
