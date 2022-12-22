
import PropTypes from 'prop-types';
import React, { useContext, useState } from 'react';
import _ from 'lodash';
import { saveAs } from 'file-saver';
import { ZapisnyListSelector } from './ZapisnyListSelector';
import { CacheRequester, Loading, RequestCache, sendRpc } from './ajax';
import { PageLayout, PageTitle } from './layout';
import { Link, QueryContext } from './router';
import { sortAs, SortableTable } from './sorting';
import { Calendar, momentLocalizer } from 'react-big-calendar';
import moment from 'moment';


// TODO: Oddelit Aktualne terminy hodnotenia vs Stare terminy hodnotenia

const MojeSkuskyColumns = [
  {
    label: (
      <React.Fragment>
        <span className="hidden-xs hidden-sm">Moje</span>?
      </React.Fragment>
    ),
    process: termin => !termin.datum_prihlasenia || termin.datum_odhlasenia ? "N" : "A",
    cell: termin => !termin.datum_prihlasenia || termin.datum_odhlasenia ? "\u2718" : "\u2714",
    colProps: termin => !termin.datum_prihlasenia || termin.datum_odhlasenia
        ? {
            title: "Nie ste prihlásení",
            className: "text-center text-negative"
          }
        : { title: "Ste prihlásení", className: "text-center text-positive" }
  },
  {
    label: "Predmet",
    prop: "nazov_predmetu",
    cell: (termin, query) => (
      <Link
        href={{
          ...query,
          modal: "detailPredmetu",
          modalPredmetKey: termin.predmet_key,
          modalAkademickyRok: termin.akademicky_rok
        }}
      >
        {termin.nazov_predmetu}
      </Link>
    ),
    expansionMark: true
  },
  { label: "Dátum",
    process: (termin) => sortAs.date(`${termin.datum} ${termin.cas}`),
    cell: (termin, query) => `${termin.datum} ${termin.cas}`
  },
  { label: "Miestnosť", prop: "miestnost", hiddenClass: ["hidden-xs"] },
  {
    label: "Hodnotiaci",
    prop: "hodnotiaci",
    process: sortAs.personName,
    hiddenClass: ["hidden-xs", "hidden-sm"]
  },
  {
    label: "Prihlásení",
    prop: "pocet_prihlasenych",
    process: sortAs.number,
    hiddenClass: ["hidden-xs"],
    cell: (termin, query) => (
      <Link
        href={{
          ...query,
          modal: "zoznamPrihlasenychNaTermin",
          modalTerminKey: termin.termin_key
        }}
      >
        {termin.pocet_prihlasenych +
          (termin.maximalne_prihlasenych
            ? "/" + termin.maximalne_prihlasenych
            : "")}
      </Link>
    )
  },
  {
    label: "Poznámka",
    prop: "poznamka",
    hiddenClass: ["hidden-xs", "hidden-sm"]
  },
  {
    label: "Prihlasovanie",
    prop: "prihlasovanie",
    process: sortAs.interval,
    hiddenClass: ["hidden-xs", "hidden-sm"]
  },
  {
    label: "Odhlasovanie",
    prop: "odhlasovanie",
    process: sortAs.interval,
    hiddenClass: ["hidden-xs", "hidden-sm"]
  },
  {
    label: "Známka",
    process: termin => termin.hodnotenie_terminu || termin.hodnotenie_predmetu,
    cell: termin => (
      <React.Fragment>
        {termin.hodnotenie_terminu
          ? termin.hodnotenie_terminu
          : termin.hodnotenie_predmetu
          ? termin.hodnotenie_predmetu + " (nepriradená k termínu)"
          : null}
        <SkuskyRegisterButton termin={termin} />
      </React.Fragment>
    )
  }
];

function convertToICAL(terminy) {
  // standard: https://tools.ietf.org/html/rfc5545
  // verificator: http://severinghaus.org/projects/icv/

  // header
  var lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//svt.fmph.uniba.sk//NONSGML votr-2017//EN",
    "X-WR-CALNAME:Moje skúšky",
    "X-WR-CALDESC:Kalendár skúšok vyexportovaný z aplikácie Votr",
    "X-WR-TIMEZONE:Europe/Bratislava",
  ];

  var dtstamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d+/, '');

  // VEVENTs
  for (var termin of terminy) {
    if (!termin.datum_prihlasenia || termin.datum_odhlasenia) {
      // nie je prihlaseny
      continue;
    }
    lines.push("BEGIN:VEVENT");

    lines.push("SUMMARY:" + termin.nazov_predmetu);

    // unique identificator for each event (so we can identify copies of the same event)
    var uid = termin.termin_key + "@votr.uniba.sk";
    lines.push("UID:" + uid);

    // DTSTAMP is when this VEVENT was created (exported), must be YYYYMMDDTHHMMSSZ
    lines.push("DTSTAMP:" + dtstamp);

    // DTSTART, DTEND
    var [den, mesiac, rok] = termin.datum.split(".");
    var [hodina, minuty] = termin.cas.split(":");
    var dtstart = `${rok}${mesiac}${den}T${hodina}${minuty}00`;

    // as for there is no info about duration, we'll set it for 4 hours
    var hodina_koniec = (parseInt(hodina) + 4).toString();
    // add leading zero
    if (hodina_koniec.length == 1) {
      hodina_koniec = "0" + hodina_koniec;
    }
    var dtend = `${rok}${mesiac}${den}T${hodina_koniec}${minuty}00`;
    lines.push("DTSTART;TZID=Europe/Bratislava:" + dtstart);
    lines.push("DTEND;TZID=Europe/Bratislava:" + dtend);

    // LOCATION
    if (termin.miestnost) {
      lines.push("LOCATION:" + termin.miestnost);
    }

    // DESCRIPTION
    //@TODO ake vsetky informacie chceme zobrazovat v popise eventu? (zatial su take, ako vo FAJR)
    var desc = "Prihlasovanie: " + termin.prihlasovanie + "\n" +
      "Odhlasovanie: " + termin.odhlasovanie + "\n" +
      "Poznámka: " + termin.poznamka;
    lines.push("DESCRIPTION:" + desc);

    lines.push("END:VEVENT");
  }

  // footer
  lines.push("END:VCALENDAR");

  return lines.map((l) => l.replace(/\n/g, "\\n")).join("\r\n");
}

function MojeSkuskyMenuLink(props) {
  return (<Link className={"btn btn-default" + (props.active ? " active" : "")} href={props.href}>{props.label}</Link>);
}

export function MojeSkuskyMenu() {
      var query = useContext(QueryContext);
      var {action, kalendar, zapisnyListKey} = query;
      return(
        <div className="pull-left">
            <div className="skusky-calendar-menu">
                <div className="btn-group">
                  <MojeSkuskyMenuLink
                    label="Zoznam"
                    href={{ action: 'mojeSkusky', kalendar: 0, zapisnyListKey }}
                    active={kalendar != 1}
                  />
                  <MojeSkuskyMenuLink
                    label="Kalendár"
                    href={{ action: 'mojeSkusky', kalendar: 1, zapisnyListKey }}
                    active={kalendar == 1}
                  />
                </div>
              </div>
        </div>)
}

function convertToEvents(terminy){
    return terminy.map((termin, i) => {
      return {id: i,
      title: `${termin.nazov_predmetu} (${termin.cas}${termin.miestnost ? ", "  + termin.miestnost : ""})`,
      start: moment(termin.datum+" "+termin.cas, 'DD.MM.YYYY HH:mm').toDate(),
      end: moment(termin.datum+" "+termin.cas, 'DD.MM.YYYY HH:mm').add(3,"hours").toDate(),
      prihlaseny: termin.datum_prihlasenia && !termin.datum_odhlasenia};
    })
}

function defaultDate(eventList) {
  var today = new Date();

  if (eventList.length) {
    var lastExamDate = _.maxBy(eventList, 'start').start;
    if (lastExamDate < today) return lastExamDate;
  }

  return today;
}

export function KalendarUdalosti(props) {
    const localizer = momentLocalizer(moment)

    return (
      <Calendar
        localizer={localizer}
        events={props.eventList}
        views={["month", "week", "day"]}
        defaultDate = {defaultDate(props.eventList)}
        className="skusky-calendar"
        messages={{
          allDay: "Celý deň",
          previous: "Späť",
          next: "Ďalej",
          today: "Dnes",
          month: "Mesiac",
          week: "Týždeň",
          day: "Deň",
          agenda: "Agenda",
          date: "Dátum",
          time: "Čas",
          event: "Skúška"
        }}
        culture={"sk"}
        eventPropGetter={
          event => {
            return {
              className: event.prihlaseny ? "skusky-calendar-registered" : "skusky-calendar-unregistered"
            };
          }
        }
        //remove start and end times (we need only one included in title)
        formats={{
          eventTimeRangeFormat: ({ start, end }, culture, local) => {}
        }}
      />
    )
}

export function MojeSkuskyPageContent() {
    var query = useContext(QueryContext);
    var cache = new CacheRequester();
    var {zapisnyListKey, kalendar} = query;

    var vidim = cache.get('get_vidim_terminy_hodnotenia', zapisnyListKey);

    if (!cache.loadedAll) {
      return <Loading requests={cache.missing} />;
    }

    if (!vidim) {
      return <p>Skúšky pre tento zápisný list už nie sú k dispozícii.</p>;
    }

    var terminyPrihlasene = cache.get('get_prihlasene_terminy', zapisnyListKey);
    var terminyVypisane = cache.get('get_vypisane_terminy', zapisnyListKey);

    if (!terminyPrihlasene || !terminyVypisane) {
      return <Loading requests={cache.missing} />;
    }

    var terminy = {};
    terminyVypisane.forEach((termin) => terminy[termin.termin_key] = termin);
    terminyPrihlasene.forEach((termin) => terminy[termin.termin_key] = termin);
    terminy = _.values(terminy);

    var message = terminy.length ? null : "Zatiaľ nie sú vypísané žiadne termíny.";

    function handleClickICal() {
      var icalText = convertToICAL(terminyPrihlasene);
      var blob = new Blob([icalText], {type: "text/calendar;charset=utf-8"});
      saveAs(blob, "MojeTerminy.ics", true);
    }

    return <React.Fragment>
      {kalendar == 1?
        <KalendarUdalosti eventList={convertToEvents(terminy)} />
        :
        <SortableTable
          items={terminy}
          columns={MojeSkuskyColumns}
          queryKey="skuskySort"
          withButtons={true}
          message={message}
          expandedContentOffset={1}
        />
      }
      {terminy.length && <button type="button" onClick={handleClickICal} className="btn">Stiahnuť ako iCal</button>}
    </React.Fragment>;
}


export function SkuskyRegisterButton({ termin }) {
  var [pressed, setPressed] = useState(false);

  var isSigninButton = !termin.datum_prihlasenia || termin.datum_odhlasenia;
  var appearDisabled = (isSigninButton && termin.moznost_prihlasit !== 'A') || pressed;

  function handleClick() {
    var command = isSigninButton ? 'prihlas_na_termin' : 'odhlas_z_terminu';

    sendRpc(command, [termin.termin_key], (message) => {
      if (message) {
        setPressed(false);
        alert(message);
      } else {
        RequestCache.invalidate('get_prihlasene_terminy');
        RequestCache.invalidate('get_vypisane_terminy');
        RequestCache.invalidate('get_prihlaseni_studenti');
      }
    });

    setPressed(true);
  }

    if (termin.hodnotenie_terminu) {
      return null;
    }

    var today = new Date().toJSON().replace(/-/g, '').substring(0, 8);
    if (today > sortAs.date(termin.datum)) return null;

    var buttonClass = "btn btn-xs " + (isSigninButton ? "btn-success" : "btn-danger") + (appearDisabled ? " appear-disabled" : "");
    var buttonText = pressed ? <Loading /> : isSigninButton ? "Prihlásiť" : "Odhlásiť";

    return <button type="button" onClick={pressed ? null : handleClick} className={buttonClass}>{buttonText}</button>;
}


export function makeMojeSkuskyPage() {
  return (
    <PageLayout>
      <ZapisnyListSelector>
        <div className="header">
          <PageTitle>Moje skúšky</PageTitle>
          <MojeSkuskyMenu />
        </div>
        <MojeSkuskyPageContent />
      </ZapisnyListSelector>
    </PageLayout>
  );
}
