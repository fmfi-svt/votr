
import { ZapisnyListSelector } from './ZapisnyListSelector';
import { CacheRequester, Loading } from './ajax';
import { PageLayout, PageTitle } from './layout';
import { Link } from './router';


export var PriebezneHodnoteniaPageContent = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },
    
  renderContent() {
    var cache = new CacheRequester();
    var {zapisnyListKey} = this.props.query;
    var [priebezneHodnotenia, message] = cache.get('get_priebezne_hodnotenia', zapisnyListKey) || [];

    if (!priebezneHodnotenia) {
      return <Loading requests={cache.missing} />;
    }
    
    if (!message && !priebezneHodnotenia.length) {
      message = "Tento zápisný list nemá žiadne priebežné hodnotenia.";
    }

    return (
      <div>
      {priebezneHodnotenia.map((priebHod) =>
        <div>
          <h2><Link href={{ ...this.props.query, modal: 'detailPredmetu', modalPredmetKey: priebHod.predmet_key, modalAkademickyRok: priebHod.akademicky_rok }}>
                {priebHod.nazov}</Link>
          </h2>
          <table className="table table-condensed table-bordered table-striped table-hover">
            <thead>
              <tr>
                <th>Dôvod hodnotenia</th>
                <th>Počet bodov / Maximum</th>
                <th>Zaevidoval</th>
                <th>Započítavať</th>
                <th>Minimum</th>
              </tr>
            </thead>
            <tbody>
            {priebHod.zaznamy.map((zaznam) =>
              <tr>
                <td>{zaznam.dovod}</td>
                <td>{zaznam.poc_bodov} / {zaznam.maximum}</td>
                <td>{zaznam.zaevidoval}</td>
                <td>{zaznam.zapocitavat}</td>
                <td>{zaznam.minimum}</td>
              </tr>
            )}
            </tbody>
          </table>
        </div>
      )}
      {message && <strong>{message}</strong>}
      </div>
    );
  },
  
  render() {
    return <div>
      <div className="header">
        <PageTitle>Priebežné hodnotenia</PageTitle>
      </div>
      {this.renderContent()}
    </div>;  
  }
});

export var PriebezneHodnoteniaPage = React.createClass({
  propTypes: {
    query: React.PropTypes.object.isRequired
  },

  render() {
    return <PageLayout query={this.props.query}>
      <ZapisnyListSelector query={this.props.query} component={PriebezneHodnoteniaPageContent} />
    </PageLayout>;
  }
});
