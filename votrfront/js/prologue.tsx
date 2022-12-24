export {};

Votr.setDebug = function (enabled) {
  document.cookie = enabled ? "votr_debug=true" : "votr_debug=";
  location.reload();
};

if (
  history.pushState &&
  window.Set &&
  window.Map &&
  Array.prototype.includes &&
  Object.values
) {
  Votr.prologueCheck = true;
} else {
  document.getElementById("votr").innerHTML = `
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
  if (window.ga) ga("send", "pageview");
}
