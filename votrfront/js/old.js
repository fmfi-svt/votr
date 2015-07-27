
if (!history.pushState) {
  document.getElementById('votr').innerHTML = `
    <div class="central-box">
    <h1>Votr</h1>
    <p>Votr ponúka študentom jednoduchší a pohodlnejší spôsob, ako robiť najčastejšie činnosti zo systému AIS.</p>
    <p>Váš prehliadač je príliš starý a nedokáže robiť všetko to, čo Votr potrebuje.</p>
    <p>Prosím stiahnite si novší prehliadač. Nové prehliadače sú rýchlejšie, pohodlnejšie a navyše bezpečnejšie.</p>
    <br>
    <ul class="list-inline">
    <li><a class="btn btn-link" href="https://www.firefox.com/">Mozilla Firefox</a>
    <li><a class="btn btn-link" href="https://www.google.com/chrome">Google Chrome</a>
    <li><a class="btn btn-link" href="https://www.opera.com/">Opera</a>
    <li><a class="btn btn-link" href="https://www.apple.com/safari/">Safari</a>
    <li><a class="btn btn-link" href="http://windows.microsoft.com/ie">Internet Explorer (10+)</a>
    </ul>
    </div>
  `;
  if (window.ga) ga('send', 'pageview');
}
