/**
 * @jsx React.DOM
 * @require jquery.min.js
 * @require react.min.js
 * @require MojePredmetyPage.js
 */

console.log('hello!');



// $('<form method="POST" action="login?server=0&type=cosigncookie&to="></form>').appendTo('body').submit()
// Votr.sendRpc('get_studia', [])
// Votr.sendRpc('get_zapisne_listy', ['INF'])


Votr.appRoot = React.renderComponent(<Votr.MojePredmetyPage route={{}} />, document.getElementById('votr'));
