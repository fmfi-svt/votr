/**
 * @require jquery.min.js
 * @require lodash.min.js
 * @require react.min.js
 * @require LoginPage.js
 * @require router.js
 * @require layout.js
 */

console.log('hello!');

function sendRpc(name, args, callback) {
  var HEADER_LENGTH = 10;
  var processed = 0;
  var result = undefined;

  function update(e) {
    while (true) {
      var waiting = xhr.responseText.length - processed;
      if (waiting < HEADER_LENGTH) break;
      var header = xhr.responseText.substr(processed, HEADER_LENGTH);
      var length = parseInt(header, HEADER_LENGTH);
      if (waiting < HEADER_LENGTH + length) break;
      var payload = xhr.responseText.substr(processed + HEADER_LENGTH, length);
      var data = JSON.parse(payload);
      console.log('RECEIVED', data);
      if (data.result) result = data.result;
      processed += HEADER_LENGTH + length;
    }
    if (xhr.readyState == 4) {
      if (processed != xhr.responseText.length) {
        console.log('INCOMPLETE!'); // TODO
      }
      if (callback) {
        callback(result);
      }
    }
  }

  function fail(e) {
    console.log("FAILED!"); // TODO
  }

  var xhr = new XMLHttpRequest();
  xhr.onload = update;
  xhr.onprogress = update;
  xhr.onerror = fail;
  xhr.open("POST", "rpc?name=" + name, true);
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.setRequestHeader("X-CSRF-Token", Votr.settings.csrf_token);
  xhr.send(JSON.stringify(args));
}

// Votr.goPost('logout')
// Votr.goPost('reset?destination=' + encodeURIComponent(location.search))

// sendRpc('get_studia', [])
// sendRpc('get_zapisne_listy', ['INF'])

(function () {

var query = Votr.settings.destination;
if (query !== undefined && (query == '' || query.substring(0, 1) == '?')) {
  try {
    history.replaceState(null, '', Votr.settings.url_root + query);
  } catch (e) {
    console.error(e);
  }
}

Votr.setDebug = function (enabled) {
  document.cookie = enabled ? 'votr_debug=true' : 'votr_debug=';
  location.reload();
}

Votr.goPost = function (url) {
  $('<form method="POST"></form>').attr('action', url).appendTo('body').submit();
};

if (Votr.settings.servers) {
  Votr.appRoot = React.renderComponent(Votr.LoginPage(), document.getElementById('votr'));
  return;
}

if (Votr.settings.error) {
  var el = document.getElementById('votr');
  $('<h1/>').text('Error').appendTo(el);
  $('<pre/>').text(Votr.settings.error).appendTo(el);
  // TODO HARDRESET button
  // TODO LOGOUT button
  return;
}

var studiaResult;
sendRpc('get_studia', [], function (result) {
  studiaResult = JSON.stringify(result);
  Votr.appRoot.forceUpdate();
});

Votr.actions['index'] = React.createClass({
  render: function () {
    return Votr.PageLayout({query: this.props.query}, React.DOM.div(null, "Index page", studiaResult));
  }
});

Votr.appRoot = React.renderComponent(Votr.App(), document.getElementById('votr'));


})();
