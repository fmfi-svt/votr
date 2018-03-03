import React, { Component } from 'react';
import FileSaver from 'file-saver';
import PropTypes from 'prop-types';

import { ZapisnyListSelector } from './ZapisnyListSelector';
import { CacheRequester, Loading, RequestCache, sendRpc } from './ajax';
import { PageLayout, PageTitle } from './layout';
import { Link } from './router';
import { sortAs, sortTable } from './sorting';


// TODO: Oddelit Aktualne terminy hodnotenia vs Stare terminy hodnotenia

export const MojeSkuskyColumns = [
  ['Moje?', null, (termin) => !termin.datum_prihlasenia || termin.datum_odhlasenia ? 'N' : 'A'],
  ['Predmet', 'nazov_predmetu'],
  ['Dátum', 'datum', sortAs.date],
  ['Čas', 'cas'],
  ['Miestnosť', 'miestnost'],
  ['Hodnotiaci', 'hodnotiaci', sortAs.personName],
  ['Prihlásení', 'pocet_prihlasenych', sortAs.number],
  ['Poznámka', 'poznamka'],
  ['Prihlasovanie', 'prihlasovanie', sortAs.interval],
  ['Odhlasovanie', 'odhlasovanie', sortAs.interval],
  ['Známka', null, (termin) => termin.hodnotenie_terminu || termin.hodnotenie_predmetu],
];

const convertToICAL = (terminy) => {
  // standard: https://tools.ietf.org/html/rfc5545
  // verificator: http://severinghaus.org/projects/icv/

  // header
  const lines = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//svt.fmph.uniba.sk//NONSGML votr-2017//EN',
    'X-WR-CALNAME:Moje skúšky',
    'X-WR-CALDESC:Kalendár skúšok vyexportovaný z aplikácie Votr',
    'X-WR-TIMEZONE:Europe/Bratislava',
  ];

  const dtstamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d+/, '');

  // VEVENTs
  for (let termin of terminy) {
    if (!termin.datum_prihlasenia || termin.datum_odhlasenia) {
      // nie je prihlaseny
      continue;
    }
    lines.push('BEGIN:VEVENT');

    lines.push('SUMMARY:' + termin.nazov_predmetu);

    // unique identificator for each event (so we can identify copies of the same event)
    const uid = termin.termin_key + '@votr.uniba.sk';
    lines.push('UID:' + uid);

    // DTSTAMP is when this VEVENT was created (exported), must be YYYYMMDDTHHMMSSZ
    lines.push('DTSTAMP:' + dtstamp);

    // DTSTART, DTEND
    const [den, mesiac, rok] = termin.datum.split('.');
    const [hodina, minuty] = termin.cas.split(':');
    const dtstart = `${rok}${mesiac}${den}T${hodina}${minuty}00`;

    // as for there is no info about duration, we'll set it for 4 hours
    let hodinaKoniec = (parseInt(hodina, 10) + 4).toString();
    // add leading zero
    if (hodinaKoniec.length === 1) {
      hodinaKoniec = '0' + hodinaKoniec;
    }
    const dtend = `${rok}${mesiac}${den}T${hodinaKoniec}${minuty}00`;
    lines.push('DTSTART;TZID=Europe/Bratislava:' + dtstart);
    lines.push('DTEND;TZID=Europe/Bratislava:' + dtend);

    // LOCATION
    if (termin.miestnost) {
      lines.push('LOCATION:' + termin.miestnost);
    }

    // DESCRIPTION
    //@TODO ake vsetky informacie chceme zobrazovat v popise eventu? (zatial su take, ako vo FAJR)
    const desc = 'Prihlasovanie: ' + termin.prihlasovanie + '\n' +
      'Odhlasovanie: ' + termin.odhlasovanie + '\n' +
      'Poznámka: ' + termin.poznamka;
    lines.push('DESCRIPTION:' + desc);

    lines.push('END:VEVENT');
  }

  // footer
  lines.push('END:VCALENDAR');

  return lines.map((l) => l.replace(/\n/g, '\\n')).join('\r\n');
};

export class MojeSkuskyPageContent extends Component {

  renderContent = () => {
    const cache = new CacheRequester();
    const { zapisnyListKey } = this.props.query;

    const vidim = cache.get('get_vidim_terminy_hodnotenia', zapisnyListKey);

    if (!cache.loadedAll) {
      return <Loading requests={cache.missing} />;
    }

    if (!vidim) {
      return <p>Skúšky pre tento zápisný list už nie sú k dispozícii.</p>;
    }

    const terminyPrihlasene = cache.get('get_prihlasene_terminy', zapisnyListKey);
    const terminyVypisane = cache.get('get_vypisane_terminy', zapisnyListKey);

    if (!terminyPrihlasene || !terminyVypisane) {
      return <Loading requests={cache.missing} />;
    }

    let terminy = {};
    terminyVypisane.forEach((termin) => {terminy[termin.termin_key] = termin;});
    terminyPrihlasene.forEach((termin) => {terminy[termin.termin_key] = termin;});
    terminy = Object.keys(terminy).map((key) => terminy[key]);

    let header;
    [terminy, header] = sortTable(
      terminy, MojeSkuskyColumns, this.props.query, 'skuskySort');

    const message = terminy.length ? null : 'Zatiaľ nie sú vypísané žiadne termíny.';

    const handleClickICal = () => {
      const icalText = convertToICAL(terminyPrihlasene);
      const blob = new Blob([icalText], { type: 'text/calendar;charset=utf-8' });
      FileSaver.saveAs(blob, 'MojeTerminy.ics', true);
    };

    return (
      <div>
        <table className="table table-condensed table-bordered table-striped table-hover with-buttons-table">
          <thead>{header}</thead>
          <tbody>
            {terminy.map((termin) => (
              <tr key={termin.termin_key}>
                {!termin.datum_prihlasenia || termin.datum_odhlasenia
                  ? <td title="Nie ste prihlásení" className="text-center text-negative">{'\u2718'}</td>
                  : <td title="Ste prihlásení" className="text-center text-positive">{'\u2714'}</td>
                }
                <td>
                  <Link
                    href={{
                      ...this.props.query,
                      modal: 'detailPredmetu',
                      modalPredmetKey: termin.predmet_key,
                      modalAkademickyRok: termin.akademicky_rok,
                    }}
                  >
                    {termin.nazov_predmetu}
                  </Link>
                </td>
                <td>{termin.datum}</td>
                <td>{termin.cas}</td>
                <td>{termin.miestnost}</td>
                <td>{termin.hodnotiaci}</td>
                <td>
                  <Link
                    href={{
                      ...this.props.query,
                      modal: 'zoznamPrihlasenychNaTermin',
                      modalTerminKey: termin.termin_key,
                    }}
                  >
                    {termin.pocet_prihlasenych +
                      (termin.maximalne_prihlasenych ? '/' + termin.maximalne_prihlasenych : '')
                    }
                  </Link>
                </td>
                <td>{termin.poznamka}</td>
                <td>{termin.prihlasovanie}</td>
                <td>{termin.odhlasovanie}</td>
                <td>
                  {termin.hodnotenie_terminu
                    ? termin.hodnotenie_terminu
                    : (
                      termin.hodnotenie_predmetu
                        ? termin.hodnotenie_predmetu + ' (nepriradená k termínu)'
                        : null
                    )
                  }
                  <SkuskyRegisterButton termin={termin} />
                </td>
              </tr>
            ))}
          </tbody>
          {message && <tfoot><tr><td colSpan={MojeSkuskyColumns.length}>{message}</td></tr></tfoot>}
        </table>
        {terminy.length && <button onClick={handleClickICal} className="btn">Stiahnuť ako iCal</button>}
      </div>
    );
  }

  render() {
    return (
      <div>
        <div className="header">
          <PageTitle>Moje skúšky</PageTitle>
        </div>
        {this.renderContent()}
      </div>
    );
  }
}

MojeSkuskyPageContent.propTypes = {
  query: PropTypes.object.isRequired,
};

export class SkuskyRegisterButton extends Component {

  componentWillMount() {
    this.setState({ pressed: false });
  }

  handleClick = () => {
    const command = this.isSigninButton() ? 'prihlas_na_termin' : 'odhlas_z_terminu';
    const termin = this.props.termin;

    sendRpc(command, [termin.termin_key], (message) => {
      if (message) {
        this.setState({ pressed: false });
        alert(message);
      } else {
        RequestCache.invalidate('get_prihlasene_terminy');
        RequestCache.invalidate('get_vypisane_terminy');
        RequestCache.invalidate('get_prihlaseni_studenti');
      }
    });

    this.setState({ pressed: true });
  }

  isDisabled = () => {
    const termin = this.props.termin;
    return (this.isSigninButton() && termin.moznost_prihlasit !== 'A') || this.state.pressed;
  }

  isSigninButton = () => {
    const termin = this.props.termin;
    return !termin.datum_prihlasenia || termin.datum_odhlasenia;
  }

  render() {
    const termin = this.props.termin;

    if (termin.hodnotenie_terminu) {
      return null;
    }

    const today = new Date()
      .toJSON()
      .replace(/-/g, '')
      .substring(0, 8);

    if (today > sortAs.date(termin.datum)) {
      return null;
    }

    const buttonClass = 'btn btn-xs '
      + (this.isSigninButton() ? 'btn-success' : 'btn-danger')
      + (this.isDisabled() ? ' appear-disabled' : '');
    const buttonText = this.state.pressed
      ? <Loading />
      : (
        this.isSigninButton()
          ? 'Prihlásiť'
          : 'Odhlásiť'
      );

    return (
      <button
        onClick={this.state.pressed ? null : this.handleClick}
        className={buttonClass}
      >
        {buttonText}
      </button>
    );
  }
}

SkuskyRegisterButton.propTypes = {
  termin: PropTypes.object.isRequired,
};

export class MojeSkuskyPage extends Component {

  render() {
    return (
      <PageLayout query={this.props.query}>
        <ZapisnyListSelector query={this.props.query} component={MojeSkuskyPageContent} />
      </PageLayout>
    );
  }
}

MojeSkuskyPage.propTypes = {
  query: PropTypes.object.isRequired,
};
