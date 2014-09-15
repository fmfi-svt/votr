/**
 * @jsx React.DOM
 * @require jquery.min.js
 * @require react.min.js
 * @require MojePredmetyPage.js
 */

console.log('hello!');



// Votr.goPost('logout')
// Votr.goPost('reset?to=' + encodeURIComponent(location.search))
// Votr.goPost('login?server=3&type=plainpassword&username=test&password=test&to=')

// Votr.sendRpc('get_studia', [])
// Votr.sendRpc('get_zapisne_listy', ['INF'])



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
    $('<input name="username" />'),
    $('<input name="password" type="password" />'),
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

Votr.appRoot = React.renderComponent(<Votr.MojePredmetyPage route={{}} />, document.getElementById('votr'));

})();
