import { pickBy } from "lodash-es";
import React, { useContext, useEffect, useMemo, useState } from "react";
import type { Href, Query } from "./types";

let trackPageViewLast: string | undefined;

function trackPageView() {
  if (!window.ga) return;
  const current =
    location.protocol +
    "//" +
    location.hostname +
    location.pathname +
    location.search;
  if (current == trackPageViewLast) return;
  trackPageViewLast = current;
  window.ga("send", "pageview", { location: current });
}

export const QueryContext = React.createContext<Query>(
  undefined as unknown as Query,
);

export function Root({ app }: { app: React.ComponentType }) {
  // eslint-disable-next-line @eslint-react/naming-convention/use-state
  const [, setState] = useState({});

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

  const queryString = location.search;

  const query = useMemo(
    () => Object.fromEntries(new URLSearchParams(queryString)),
    [queryString],
  );

  const C = app;
  return (
    <QueryContext value={query}>
      <C />
    </QueryContext>
  );
}

// https://github.com/microsoft/TypeScript/issues/16069
// https://github.com/microsoft/TypeScript/issues/38390
// https://stackoverflow.com/questions/43010737/way-to-tell-typescript-compiler-array-prototype-filter-removes-certain-types-fro
function isNotNullOrUndefined<T>(arg: T | null | undefined): arg is T {
  return arg != null;
}

export function buildUrl(href: string | Href) {
  if (typeof href == "string") return href;
  // omitBy(isUndefined) works too but lodash TypeScript typings don't handle
  // type guards on omitBy, only on pickBy.
  return "?" + String(new URLSearchParams(pickBy(href, isNotNullOrUndefined)));
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
  >,
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
  const query = useContext(QueryContext);
  return <Link {...rest} href={{ ...query, ...href }} />;
}

// Looks and acts like a link, but doesn't have a href and cannot be opened in
// a new tab when middle-clicked or ctrl-clicked.
export function FakeLink(
  props: {
    onClick: (event: React.KeyboardEvent) => void;
  } & React.HTMLAttributes<HTMLAnchorElement>,
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
