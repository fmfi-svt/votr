/**
 * @require jquery.min.js
 * @require react.min.js
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
// Votr.goPost('login?server=3&type=plainpassword&username=test&password=test&destination=')

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

Votr.goPost = function (url) {
  $('<form method="POST"></form>').attr('action', url).appendTo('body').submit();
};

if (!Votr.settings.csrf_token) {
  var el = document.getElementById('votr');
  $('<h1/>').text('Login').appendTo(el);
  if (Votr.settings.invalid_session) $('<p/>').text('Invalid or expired session.').appendTo(el);
  if (Votr.settings.error) $('<pre/>').text(Votr.settings.error).appendTo(el);
  $('<form action="login" method="POST" />').appendTo(el).append(
    $('<input name="destination" type="hidden" />').val(location.search),
    $('<input name="server" value="0" />'),
    $('<input name="type" value="cosigncookie" />'),
    $('<input name="cookie" />'),
    $('<input name="username" />'),
    $('<input name="password" type="password" />'),
    $('<input type="submit" value="OK" />')
  );
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

sendRpc('get_studia', [], function (result) {
  document.getElementById('votr').textContent = JSON.stringify(result);
});

})();
