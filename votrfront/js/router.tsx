import $ from "jquery";
import { isUndefined, omitBy } from "lodash-es";
import React, { useContext, useEffect, useMemo, useState } from "react";
import { Href, Query } from "./types";

var trackPageViewLast: string | undefined;

function trackPageView() {
  if (!window.ga) return;
  var current =
    location.protocol +
    "//" +
    location.hostname +
    location.pathname +
    location.search;
  if (current == trackPageViewLast) return;
  trackPageViewLast = current;
  window.ga("send", "pageview", { location: current });
}

function parseQueryString(queryString: string) {
  if (!queryString) return {};
  var result: Query = {};
  var pairs = queryString.split("&");
  for (const pair of pairs) {
    var index = pair.indexOf("=");
    if (index == -1) {
      index = pair.length;
    }
    var name = pair.substring(0, index);
    var value = pair.substring(index + 1);
    result[name] = decodeURIComponent(value.replace(/\+/g, " "));
  }
  return result;
}

export var QueryContext = React.createContext<Query>(
  undefined as unknown as Query
);

export function Root({ app }: { app: React.ComponentType }) {
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

    window.addEventListener("popstate", handlePopState, false);
    return () => window.removeEventListener("popstate", handlePopState, false);
  }, []);

  useEffect(() => {
    trackPageView();
  });

  var queryString = location.search.substring(1);

  var query = useMemo(() => parseQueryString(queryString), [queryString]);

  var C = app;
  return (
    <QueryContext.Provider value={query}>
      <C />
    </QueryContext.Provider>
  );
}

export function buildUrl(href: string | Href) {
  if (typeof href == "string") return href;
  return "?" + $.param(omitBy(href, isUndefined), true);
}

export function navigate(href: string | Href) {
  Votr.didNavigate = true;
  history.pushState(null, "", Votr.settings.url_root + buildUrl(href));
  Votr.updateRoot();
}

export function Link(
  props: { href: string | Href } & Omit<
    React.AnchorHTMLAttributes<HTMLAnchorElement>,
    "href"
  >
) {
  function handleClick(event: React.MouseEvent) {
    // Chrome fires onclick on middle click. Firefox only fires it on document,
    // see <http://lists.w3.org/Archives/Public/www-dom/2013JulSep/0203.html>,
    // but React adds event listeners to document so we still see a click event.
    if (event.button != 0) return;

    event.preventDefault();
    navigate(props.href);
  }

  return <a {...props} href={buildUrl(props.href)} onClick={handleClick} />;
}

export function RelativeLink({
  href,
  ...rest
}: { href: Href } & Omit<React.HTMLAttributes<HTMLAnchorElement>, "href">) {
  var query = useContext(QueryContext);
  return <Link {...rest} href={{ ...query, ...href }} />;
}

// Looks and acts like a link, but doesn't have a href and cannot be opened in
// a new tab when middle-clicked or ctrl-clicked.
export function FakeLink(
  props: {
    onClick: (event: React.KeyboardEvent) => void;
  } & React.HTMLAttributes<HTMLAnchorElement>
) {
  // Pressing Enter on <a href=...> emits a click event, and the HTML5 spec
  // says elements with tabindex should do that too, but they don't.
  // <http://www.w3.org/TR/WCAG20-TECHS/SCR29> suggests using a keyup event:
  function handleKeyUp(event: React.KeyboardEvent) {
    if (event.which == 13) {
      event.preventDefault();
      props.onClick(event);
    }
  }

  return <a {...props} onKeyUp={handleKeyUp} tabIndex={0} role="button" />;
}

Votr.dev_navigate = navigate;
