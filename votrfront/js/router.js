
import PropTypes from 'prop-types';
import React from 'react';
import _ from 'lodash';
import $ from 'jquery';

export function trackPageView() {
  if (!window.ga) return;
  var current = location.protocol + '//' + location.hostname +
                location.pathname + location.search;
  if (current == trackPageView.last) return;
  trackPageView.last = current;
  ga('send', 'pageview', { location: current });
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


export var QueryContext = React.createContext();


export class Root extends React.Component {
  handlePopState = () => {
    Votr.appRoot.forceUpdate();
  }

  componentDidMount() {
    Votr.appRoot = this;
    window.addEventListener('popstate', this.handlePopState, false);
    trackPageView();
  }

  componentDidUpdate() {
    trackPageView();
  }

  render() {
    var queryString = location.search.substring(1);
    if (queryString !== this.lastQueryString) {
      this.query = parseQueryString(queryString);
      this.lastQueryString = queryString;
    }

    return (
      <React.StrictMode>
        <QueryContext.Provider value={this.query}>
          <this.props.app />
        </QueryContext.Provider>
      </React.StrictMode>
    );
  }
}


export function buildUrl(href) {
  if (_.isString(href)) return href;
  return '?' + $.param(_.omitBy(href, _.isUndefined), true);
};


export function navigate(href) {
  Votr.didNavigate = true;
  history.pushState(null, '', Votr.settings.url_root + buildUrl(href));
  Votr.appRoot.forceUpdate();
};


export function Link(props) {
  function handleClick(event) {
    // Chrome fires onclick on middle click. Firefox only fires it on document,
    // see <http://lists.w3.org/Archives/Public/www-dom/2013JulSep/0203.html>,
    // but React adds event listeners to document so we still see a click event.
    if (event.button != 0) return;

    event.preventDefault();
    navigate(props.href);
  }

  return <a {...props} href={buildUrl(props.href)} onClick={handleClick} />;
}


// Looks and acts like a link, but doesn't have a href and cannot be opened in
// a new tab when middle-clicked or ctrl-clicked.
export function FakeLink(props) {
  // Pressing Enter on <a href=...> emits a click event, and the HTML5 spec
  // says elements with tabindex should do that too, but they don't.
  // <http://www.w3.org/TR/WCAG20-TECHS/SCR29> suggests using a keyup event:
  function handleKeyUp(event) {
    if (event.which == 13) {
      event.preventDefault();
      props.onClick(event);
    }
  }

  return <a {...props} onKeyUp={handleKeyUp} tabIndex="0" role="button" />;
}

FakeLink.propTypes = {
  onClick: PropTypes.func.isRequired
};
