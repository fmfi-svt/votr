/**
 * @jsx React.DOM
 * @require react.min.js
 */

(function () {


Votr.translate = function (str) {
  return str;
}

var t = Votr.t = function (props, child) {
  if (arguments.length == 1 && typeof props === 'string') {
    return Votr.translate(props);
  }

  if (props !== null) throw Error("<t> cannot have props");
  if (arguments.length != 2) throw Error("<t> requires a single child");
  if (typeof child !== 'string') throw Error("<t> requires string content");
  return Votr.translate(child);
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
