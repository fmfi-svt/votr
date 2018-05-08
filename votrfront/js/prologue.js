
Votr.setDebug = function (enabled) {
  document.cookie = enabled ? 'votr_debug=true' : 'votr_debug=';
  location.reload();
}

if (!history.pushState || !window.Set || !window.Map) {
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
    <li><a class="btn btn-link" href="http://windows.microsoft.com/ie">Internet Explorer 11</a>
    </ul>
    </div>
  `;
  if (window.ga) ga('send', 'pageview');
}

window.addEventListener('load', function () {
var RequestCache;
for (var k in Votr.webpackRequire.c) {
  if (Votr.webpackRequire.c[k].exports.RequestCache) {
    RequestCache = Votr.webpackRequire.c[k].exports.RequestCache;
  }
}
if (!RequestCache) throw Error('wat');

var inp = document.createElement('input');
inp.type = 'file';
inp.onchange = function () {
  if (!this.files[0]) return;
  var reader = new FileReader();
  reader.onload = function (event) {
    for (var k in RequestCache) {
      if (k != 'pending' && k != 'sendRequest' && k != 'invalidate') {
        delete RequestCache[k];
      }
    }
    RequestCache.sendRequest = function (request) {
      var cacheKey = request.join('\0');
      if (RequestCache[cacheKey]) return;
      if (RequestCache.pending[cacheKey]) return;
      RequestCache.pending[cacheKey] = true;
    };

    var requests;
    var currentKey;
    for (var line of reader.result.split('\n')) {
      if (!line) continue;
      var info = JSON.parse(line);
      if (info[1] != 'rpc') continue;
      if (info[2].endsWith(' started')) {
        info[3].unshift(info[2].split(' ')[1]);
        currentKey = info[3].join('\0');
      }
      if (info[2].endsWith(' finished')) {
        RequestCache[currentKey] = info[3];
      }
    }
  };
  reader.readAsText(this.files[0]);
};
document.body.appendChild(inp);
});
