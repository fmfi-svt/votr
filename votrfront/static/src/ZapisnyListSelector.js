/**
 * @jsx React.DOM
 * @require base.js
 * @require ajax.js
 * @require structures.js
 * @require react.min.js
 */

(function () {

var {CacheRequester, Loading, convertStudium, convertZapisnyList} = Votr;


function dateToInteger(date) {
  if (date == '') return 0;
  if (!date.match(/^\d\d\.\d\d\.\d\d\d\d$/)) throw Error('Bad date format');
  return parseInt(
    date.substring(6, 10) + date.substring(3, 5) + date.substring(0, 2), 10);
}


Votr.ZapisnyListSelector = React.createClass({
  propTypes: {
    route: React.PropTypes.object.isRequired,
    component: React.PropTypes.func.isRequired
  },

  render: function () {
    var {studiumKey, zapisnyListKey} = this.props.route;

    var cache = new CacheRequester();
    var studia = cache.get('get_studia');

    var selectorContent = [];
    var latestDate = -1, latestStudiumKey, latestZapisnyListKey;

    if (studia) studia.map(convertStudium).forEach((studium) => {
      var zapisneListy = cache.get('get_zapisne_listy', studium.key);
      if (zapisneListy) zapisneListy.map(convertZapisnyList).forEach((zapisnyList) => {
        selectorContent.push(
          <span key={zapisnyList.key}
                className={zapisnyList.key == zapisnyListKey ? "selected" : ""}>
            {zapisnyList.akademicky_rok} {zapisnyList.sp_skratka}
          </span>);

        var date = dateToInteger(zapisnyList.datum_zapisu);
        if (date > latestDate) {
          latestDate = date;
          latestStudiumKey = studium.key;
          latestZapisnyListKey = zapisnyList.key;
        }
      });
    });

    var selector = <div className="selector">
      {selectorContent}
      {cache.loadedAll ? null : <Loading requests={cache.missing} />}
    </div>;

    if (!(studiumKey && zapisnyListKey) && latestStudiumKey && cache.loadedAll) {
      studiumKey = latestStudiumKey;
      zapisnyListKey = latestZapisnyListKey;
    }

    var page = null;
    if (zapisnyListKey && studiumKey) {
      page = <this.props.component zapisnyListKey={zapisnyListKey} studiumKey={studiumKey} />;
    } else if (cache.loadedAll && selectorContent.length == 0) {
      page = <div><t>Žiadne zápisné listy.</t></div>;
    }

    return <div>
      {selector}
      {page}
    </div>;
  }
});


})();
