/* eslint-disable @typescript-eslint/no-unnecessary-condition, @typescript-eslint/prefer-optional-chain */

export {};

if (window.console && window.console.log) {
  window.console.log(
    "Beží %c%s%c JavaScript build. %s",
    "font-weight: bold",
    process.env.NODE_ENV,
    "",
    Votr.settings.both_js
      ? "Prepínateľné s: Votr.setJsDev(true alebo false)"
      : "Nejde prepínať, nemáme yarn buildboth."
  );
}

Votr.setJsDev = function (enabled: unknown) {
  document.cookie =
    Votr.settings.instance_name + "_jsdev=" + (enabled ? "true" : "");
  location.reload();
};

if (
  // @ts-expect-error TS2774
  history.pushState &&
  window.Set &&
  window.Map &&
  // @ts-expect-error TS2774
  Array.prototype.includes &&
  // @ts-expect-error TS2774
  Object.values
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
