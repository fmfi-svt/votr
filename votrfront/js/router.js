
import PropTypes from 'prop-types';
import React, { useEffect, useMemo, useState } from 'react';
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


export function Root({ app }) {
  var [, setState] = useState({});

  useEffect(() => {
    Votr.updateRoot = () => {
      // Don't use `setState(state => !state)` as a forceUpdate alternative!
      // It won't update if called twice before React schedules a rerender,
      // because state wraps back to the old value. Especially twice in one
      // tick, but the scheduler can be random. (Maybe only with StrictMode
      // in the development build.)
      setState({});
    };

    function handlePopState() {
      Votr.updateRoot();
    }

    window.addEventListener('popstate', handlePopState, false);
    return () => window.removeEventListener('popstate', handlePopState, false);
  }, []);

  useEffect(() => {
    trackPageView();
  });

  var queryString = location.search.substring(1);

  var query = useMemo(() => parseQueryString(queryString), [queryString]);

  var C = app;
  return <QueryContext.Provider value={query}><C /></QueryContext.Provider>;
}


export function buildUrl(href) {
  if (_.isString(href)) return href;
  return '?' + $.param(_.omitBy(href, _.isUndefined), true);
};


export function navigate(href) {
  Votr.didNavigate = true;
  history.pushState(null, '', Votr.settings.url_root + buildUrl(href));
  Votr.updateRoot();
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
