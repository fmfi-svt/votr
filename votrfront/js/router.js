
export function trackPageView() {
  if (!window.ga) return;
  var current = location.protocol + '//' + location.hostname +
                location.pathname + location.search;
  if (current == trackPageView.last) return;
  trackPageView.last = current;
  ga('send', 'pageview', { location: current });
};


export var AnalyticsMixin = {
  componentDidMount() {
    trackPageView();
  },

  componentDidUpdate() {
    trackPageView();
  }
};


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


export var Root = React.createClass({
  mixins: [AnalyticsMixin],

  handlePopState() {
    this.forceUpdate();
  },

  componentDidMount() {
    window.addEventListener('popstate', this.handlePopState, false);
  },

  render() {
    var queryString = location.search.substring(1);
    if (queryString !== this.lastQueryString) {
      this.query = parseQueryString(queryString);
      this.lastQueryString = queryString;
    }

    return <this.props.app query={this.query} />;
  }
});


export function buildUrl(href) {
  if (_.isString(href)) return href;
  return '?' + $.param(_.omit(href, _.isUndefined), true);
};


export function navigate(href) {
  Votr.didNavigate = true;
  history.pushState(null, '', Votr.settings.url_root + buildUrl(href));
  Votr.appRoot.forceUpdate();
};


export var Link = React.createClass({
  handleClick(event) {
    // Chrome fires onclick on middle click. Firefox only fires it on document,
    // see <http://lists.w3.org/Archives/Public/www-dom/2013JulSep/0203.html>,
    // but React adds event listeners to document so we still see a click event.
    if (event.button != 0) return;

    event.preventDefault();
    navigate(this.props.href);
  },

  render() {
    return <a {...this.props} href={buildUrl(this.props.href)}
              onClick={this.handleClick} />;
  }
});


// Looks and acts like a link, but doesn't have a href and cannot be opened in
// a new tab when middle-clicked or ctrl-clicked.
export var FakeLink = React.createClass({
  propTypes: {
    onClick: React.PropTypes.func.isRequired
  },

  // Pressing Enter on <a href=...> emits a click event, and the HTML5 spec
  // says elements with tabindex should do that too, but they don't.
  // <http://www.w3.org/TR/WCAG20-TECHS/SCR29> suggests using a keyup event:
  handleKeyUp(event) {
    if (event.which == 13) {
      event.preventDefault();
      this.props.onClick(event);
    }
  },

  render() {
    return <a {...this.props} onKeyUp={this.handleKeyUp}
              tabIndex="0" role="button" />;
  }
});
