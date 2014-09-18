/** @jsx React.DOM */

(function () {


Votr.MojeSkuskyPageContent = React.createClass({
  render: function () {
    var cache = new Votr.CacheRequester();
    var skusky = cache.get('get_prihlasene_terminy', this.props.query.studiumKey, this.props.query.zapisnyListKey);
    return <div>
      <p>Studium key: {this.props.query.studiumKey}</p>
      <p>Zapisny list key: {this.props.query.zapisnyListKey}</p>
      <p>Moje skusky: {skusky ? JSON.stringify(skusky) : <Votr.Loading requests={cache.missing} />}</p>
    </div>;
  }
});


Votr.MojeSkuskyPage = React.createClass({
  render: function () {
    return <Votr.PageLayout query={this.props.query}>
      <Votr.ZapisnyListSelector query={this.props.query} component={Votr.MojeSkuskyPageContent} />
    </Votr.PageLayout>;
  }
});


})();
