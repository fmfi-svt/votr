/** @jsx React.DOM */

(function () {


Votr.TestPage = React.createClass({
  render: function () {
    return <Votr.PageLayout query={this.props.query}>
      <p></p>
    </Votr.PageLayout>
  }
});


Votr.actions = {
  index: Votr.TestPage,
  mojeHodnotenia: Votr.MojeHodnoteniaPage,
  mojePredmety: Votr.MojePredmetyPage,
  mojeSkusky: Votr.MojeSkuskyPage,
  zoznamPrihlasenychNaTermin: Votr.ZoznamPrihlasenychNaTerminPage
};


})();
