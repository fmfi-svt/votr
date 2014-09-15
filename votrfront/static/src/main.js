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
  xhr.send(JSON.stringify(args));
}

// Votr.goPost('logout')
// Votr.goPost('reset?to=' + encodeURIComponent(location.search))
// Votr.goPost('login?server=3&type=plainpassword&username=test&password=test&to=')

// sendRpc('get_studia', [])
// sendRpc('get_zapisne_listy', ['INF'])

(function () {

if (Votr.destination !== undefined && (Votr.destination == '' || Votr.destination.substring(0, 1) == '?')) {
  try {
    history.replaceState(null, '', Votr.url_root + Votr.destination);
  } catch (e) {
    console.error(e);
  }
}

Votr.goPost = function (url) {
  $('<form method="POST"></form>').attr('action', url).appendTo('body').submit();
};

if (Votr.login) {
  var el = document.getElementById('votr');
  $('<h1/>').text('Login').appendTo(el);
  if (Votr.invalid_session) $('<p/>').text('Invalid or expired session.').appendTo(el);
  if (Votr.error) $('<pre/>').text(Votr.error).appendTo(el);
  $('<form action="login" method="POST" />').appendTo(el).append(
    $('<input name="to" type="hidden" />').val(location.search),
    $('<input name="server" value="0" />'),
    $('<input name="type" value="cosigncookie" />'),
    $('<input name="cookie" />'),
    $('<input type="submit" value="OK" />')
  );
  return;
}

if (Votr.error) {
  var el = document.getElementById('votr');
  $('<h1/>').text('Error').appendTo(el);
  $('<pre/>').text(Votr.error).appendTo(el);
  // TODO HARDRESET button
  // TODO LOGOUT button
  return;
}

sendRpc('get_studia', [], function (result) {
  document.getElementById('votr').textContent = JSON.stringify(result);
});

})();
