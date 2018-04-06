
import { ZapisnyListSelector } from './ZapisnyListSelector';
import { CacheRequester, Loading } from './ajax';
import { PageLayout, PageTitle } from './layout';
import { Link, queryConsumer } from './router';
import { humanizeBoolean } from './humanizeAISData';


export function PriebezneHodnoteniaPageContent() {
  return queryConsumer(query => {
    var cache = new CacheRequester();
    var {zapisnyListKey} = query;
    var [priebezneHodnotenia, message] = cache.get('get_priebezne_hodnotenia', zapisnyListKey) || [];

    if (!priebezneHodnotenia) {
      return <Loading requests={cache.missing} />;
    }
    
    if (!message && !priebezneHodnotenia.length) {
      message = "Tento zápisný list nemá žiadne priebežné hodnotenia.";
    }

    return (
      <React.Fragment>
      {priebezneHodnotenia.map((priebHod) =>
        <React.Fragment>
          <h2><Link href={{ ...query, modal: 'detailPredmetu', modalPredmetKey: priebHod.predmet_key, modalAkademickyRok: priebHod.akademicky_rok }}>
                {priebHod.nazov}</Link>
          </h2>
          <table className="table table-condensed table-bordered table-striped table-hover">
            <thead>
              <tr>
                <th>Popis</th>
                <th>Body</th>
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
                <td>{humanizeBoolean(zaznam.zapocitavat)}</td>
                <td>{zaznam.minimum}</td>
              </tr>
            )}
            </tbody>
          </table>
        </React.Fragment>
      )}
      {message && <strong>{message}</strong>}
      </React.Fragment>
    );
  });
}


export function PriebezneHodnoteniaPage() {
  return (
    <PageLayout>
      <ZapisnyListSelector>
        <div className="header">
          <PageTitle>Priebežné hodnotenia</PageTitle>
        </div>
        <PriebezneHodnoteniaPageContent />
      </ZapisnyListSelector>
    </PageLayout>
  );
}
