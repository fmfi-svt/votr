import React, { useContext } from "react";
import { CacheRequester, Loading } from "./ajax";
import { humanizeBoolean } from "./humanizeAISData";
import { PageLayout, PageTitle } from "./layout";
import { QueryContext, RelativeLink } from "./router";
import { ZapisnyListSelector } from "./ZapisnyListSelector";

function PriebezneHodnoteniaPageContent() {
  var query = useContext(QueryContext);
  var cache = new CacheRequester();
  var zapisnyListKey = query.zapisnyListKey!;

  var [priebezneHodnotenia, message] =
    cache.get("get_priebezne_hodnotenia", zapisnyListKey) || [];

  if (!priebezneHodnotenia) {
    return <Loading requests={cache.missing} />;
  }

  if (!message && !priebezneHodnotenia.length) {
    message = "Tento zápisný list nemá žiadne priebežné hodnotenia.";
  }

  return (
    <React.Fragment>
      {priebezneHodnotenia.map((priebHod, index) => (
        <React.Fragment key={index}>
          <h2>
            <RelativeLink
              href={{
                modal: "detailPredmetu",
                modalPredmetKey: priebHod.predmet_key,
                modalAkademickyRok: priebHod.akademicky_rok,
              }}
            >
              {priebHod.nazov}
            </RelativeLink>
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
              {priebHod.zaznamy.map((zaznam, zaznamIndex) => (
                <tr key={zaznamIndex}>
                  <td>{zaznam.dovod}</td>
                  <td>
                    {zaznam.poc_bodov} / {zaznam.maximum}
                  </td>
                  <td>{zaznam.zaevidoval}</td>
                  <td>{humanizeBoolean(zaznam.zapocitavat)}</td>
                  <td>{zaznam.minimum}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </React.Fragment>
      ))}
      {!!message && <strong>{message}</strong>}
    </React.Fragment>
  );
}

export function makePriebezneHodnoteniaPage() {
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
