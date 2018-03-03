import React, { Component } from 'react';
import PropTypes from 'prop-types';
import $ from 'jquery';

export function trackPageView() {
  if (!window.ga) return;
  const current = location.protocol + '//' + location.hostname +
                location.pathname + location.search;
  if (current === trackPageView.last) return;
  trackPageView.last = current;
  ga('send', 'pageview', { location: current });
};


export const AnalyticsMixin = {
  componentDidMount() {
    trackPageView();
  },

  componentDidUpdate() {
    trackPageView();
  },
};


const parseQueryString = (queryString) => {
  if (!queryString) return {};
  const result = {};
  const pairs = queryString.split('&');
  for (let i = 0; i < pairs.length; i++) {
    let index = pairs[i].indexOf('=');
    if (index === -1) {
      index = pairs[i].length;
    }
    const name = pairs[i].substring(0, index);
    const value = pairs[i].substring(index + 1);
    result[name] = decodeURIComponent(value.replace(/\+/g, ' '));
  }
  return result;
};

export class Root extends Component {

  handlePopState = () => {
    this.forceUpdate();
  }

  componentDidMount() {
    window.addEventListener('popstate', this.handlePopState, false);
  }

  render() {
    const queryString = location.search.substring(1);
    if (queryString !== this.lastQueryString) {
      this.query = parseQueryString(queryString);
      this.lastQueryString = queryString;
    }

    return <this.props.app query={this.query} />;
  }
}

Root.mixins = [AnalyticsMixin];

export const buildUrl = (href) => {
  if (typeof href === 'string' || href instanceof String) {
    return href;
  }
  // remove empty query paramaters
  const newHref = Object.keys(href)
    .filter((key) => key !== undefined)
    .reduce(
      (newObj, key) => {
        newObj[key] = href[key];
        return newObj;
      },
      {}
    );

  return '?' + $.param(newHref, true);
};

export const navigate = (href) => {
  Votr.didNavigate = true;
  history.pushState(null, '', Votr.settings.url_root + buildUrl(href));
  Votr.appRoot.forceUpdate();
};

export class Link extends Component {
  handleClick = (event) => {
    // Chrome fires onclick on middle click. Firefox only fires it on document,
    // see <http://lists.w3.org/Archives/Public/www-dom/2013JulSep/0203.html>,
    // but React adds event listeners to document so we still see a click event.
    if (event.button !== 0) {
      return;
    }

    event.preventDefault();
    navigate(this.props.href);
  }

  render() {
    return (
      <a
        {...this.props}
        href={buildUrl(this.props.href)}
        onClick={this.handleClick}
      />
    );
  }
}


// Looks and acts like a link, but doesn't have a href and cannot be opened in
// a new tab when middle-clicked or ctrl-clicked.
export class FakeLink extends Component {

  // Pressing Enter on <a href=...> emits a click event, and the HTML5 spec
  // says elements with tabindex should do that too, but they don't.
  // <http://www.w3.org/TR/WCAG20-TECHS/SCR29> suggests using a keyup event:
  handleKeyUp = (event) => {
    if (event.which === 13) {
      event.preventDefault();
      this.props.onClick(event);
    }
  }

  render() {
    return (
      <a
        {...this.props}
        onKeyUp={this.handleKeyUp}
        tabIndex="0"
        role="button"
      />
    );
  }
}

FakeLink.propTypes = {
  onClick: PropTypes.func.isRequired,
};
