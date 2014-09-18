/**
 * @jsx React.DOM
 */

(function () {


function parseQueryString(queryString) {
  if (!queryString) return {};
  var result = {};
  var pairs = queryString.split('&');
  for (var i = 0; i < pairs.length; i++) {
    var index = pairs[i].indexOf('=');
    if (index == -1) {
      index = pairs[i].length;
    }
    var name = pairs[i].substring(0, index);
    var value = pairs[i].substring(index + 1);
    result[name] = decodeURIComponent(value.replace(/\+/g, ' '));
  }
  return result;
}


Votr.NotFoundPage = React.createClass({
  render: function () {
    // TODO: Proper page style and navigation.
    return <div>Action not found!</div>;
  }
});


Votr.App = React.createClass({
  handlePopState: function () {
    this.forceUpdate();
  },

  componentDidMount: function () {
    window.addEventListener('popstate', this.handlePopState, false);
  },

  render: function () {
    var queryString = location.search.substring(1);
    if (queryString !== this.lastQueryString) {
      this.query = parseQueryString(queryString);
      this.lastQueryString = queryString;
    }

    var action = this.query.action || 'index';
    var component = this.props.actions[action] || Votr.NotFoundPage;
    return <component query={this.query} />;
  }
});


Votr.buildUrl = function (href) {
  if (_.isString(href)) return href;
  return '?' + $.param(_.omit(href, _.isUndefined), true);
};


Votr.navigate = function (href) {
  history.pushState(null, '', Votr.settings.url_root + Votr.buildUrl(href));
  Votr.appRoot.forceUpdate();
};


Votr.Link = React.createClass({
  handleClick: function (event) {
    // Chrome fires onclick on middle click. Firefox only fires it on document,
    // see <http://lists.w3.org/Archives/Public/www-dom/2013JulSep/0203.html>,
    // but React adds event listeners to document so we still see a click event.
    if (event.button != 0) return;

    event.preventDefault();
    Votr.navigate(this.props.href);
  },

  render: function () {
    return this.transferPropsTo(
        <a href={Votr.buildUrl(this.props.href)} onClick={this.handleClick}>
          {this.props.children}
        </a>);
  }
});


})();
