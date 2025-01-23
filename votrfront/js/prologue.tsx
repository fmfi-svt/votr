/* eslint-disable @typescript-eslint/no-unnecessary-condition */

export {};

try {
  console.log(
    "Beží %c%s%c JavaScript build. %s",
    "font-weight: bold",
    process.env.NODE_ENV,
    "",
    Votr.settings.both_js
      ? "Prepínateľné s: Votr.setJsDev(true alebo false)"
      : "Nejde prepínať, nemáme 'buildboth'."
  );
  // Don't omit `(e)` because the prologue should work in old browsers.
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
} catch (e) {
  // Ignore errors.
}

Votr.setJsDev = function (enabled: unknown) {
  document.cookie =
    Votr.settings.instance_id + "_jsdev=" + (enabled ? "true" : "");
  location.reload();
};

// Current bottleneck:
// Object.fromEntries - https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/fromEntries
//
// Which means:
// Chrome 73+ (2019), Edge 79+ (2020), Firefox 63+ (2018), Opera 60+ (2019), Safari 12.1+ (2019), Safari iOS 12.2+ (2019)
//
// Therefore we should be able to use e.g.:
// URLSearchParams record for init object - https://developer.mozilla.org/en-US/docs/Web/API/URLSearchParams/URLSearchParams#browser_compatibility
// Spread in object literals - https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Spread_syntax#browser_compatibility
// Rest in objects - https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Destructuring_assignment#browser_compatibility
// Object.values - https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/values
// String padStart - https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/String/padStart
// history.pushState, Map, Set, Object.values, ...
//
// When updating, remember to look at tsconfig.json (target) and package.json (browserslist).
// TODO: If we get Array#at (ES2022) one day, we can use it instead of lodash _.last().

if (
  window.URLSearchParams &&
  // @ts-expect-error: TS2774 because we're doing feature detection
  Object.fromEntries
) {
  Votr.prologueCheck = true;
} else {
  document.getElementById("votr")!.innerHTML = `
    <div class="central-box">
    <h1>Votr</h1>
    <p>Votr ponúka študentom jednoduchší a pohodlnejší spôsob, ako robiť najčastejšie činnosti zo systému AIS.</p>
    <p>Váš prehliadač je príliš starý a nedokáže robiť všetko to, čo Votr potrebuje.</p>
    <p>Prosím stiahnite si novší prehliadač. Nové prehliadače sú rýchlejšie, pohodlnejšie a navyše bezpečnejšie.</p>
    <br>
    <ul class="list-inline">
    <li><a class="btn btn-link" href="https://www.firefox.com/">Firefox</a>
    <li><a class="btn btn-link" href="https://www.google.com/chrome">Chrome</a>
    <li><a class="btn btn-link" href="https://www.opera.com/">Opera</a>
    <li><a class="btn btn-link" href="https://www.apple.com/safari/">Safari</a>
    <li><a class="btn btn-link" href="https://www.microsoft.com/en-us/edge">Edge</a>
    </ul>
    </div>
  `;
  if (window.ga) window.ga("send", "pageview");
}
