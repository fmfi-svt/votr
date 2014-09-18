/**
 * @jsx React.DOM
 * @require layout.js
 * @require MojeSkuskyPage.js
 */

(function () {


Votr.TestPage = React.createClass({
  render: function () {
    return <Votr.PageLayout query={this.props.query}>
      <p>Action is: "{this.props.query.action}"</p>
    </Votr.PageLayout>
  }
});


Votr.actions = {
  index: Votr.TestPage,
  mojePredmety: Votr.TestPage,
  mojeSkusky: Votr.MojeSkuskyPage
};


})();
