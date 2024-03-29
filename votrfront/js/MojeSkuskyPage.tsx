import classNames from "classnames";
import { saveAs } from "file-saver";
import _ from "lodash";
import moment from "moment";
import React, { useContext, useState } from "react";
import { Calendar, momentLocalizer } from "react-big-calendar";
import {
  CacheRequester,
  invalidateRequestCache,
  Loading,
  sendRpc,
} from "./ajax";
import { PageLayout, PageTitle } from "./layout";
import { underSM, underXS } from "./mediaQueries";
import { Link, QueryContext, RelativeLink } from "./router";
import { Column, column, SortableTable, sortAs } from "./sorting";
import { Href, Termin } from "./types";
import { ZapisnyListSelector } from "./ZapisnyListSelector";

// TODO: Oddelit Aktualne terminy hodnotenia vs Stare terminy hodnotenia

function somPrihlaseny(termin: Termin) {
  return !!termin.datum_prihlasenia && !termin.datum_odhlasenia;
}

const MojeSkuskyColumns: Column<Termin>[] = [
  column({
    label: (
      <React.Fragment>
        <span className="hidden-xs hidden-sm">Moje</span>?
      </React.Fragment>
    ),
    projection: somPrihlaseny,
    sortKey: (value: boolean) => (value ? "A" : "N"),
    display: (value: boolean) => (value ? "\u2714" : "\u2718"),
    cellProps: (value: boolean) => ({
      title: value ? "Ste prihlásení" : "Nie ste prihlásení",
      className: classNames(
        "text-center",
        value ? "text-positive" : "text-negative"
      ),
    }),
  }),
  column({
    label: "Predmet",
    sortKey: (termin: Termin) => termin.nazov_predmetu,
    display: (termin: Termin) => (
      <RelativeLink
        href={{
          modal: "detailPredmetu",
          modalPredmetKey: termin.predmet_key,
          modalAkademickyRok: termin.akademicky_rok,
        }}
      >
        {termin.nazov_predmetu}
      </RelativeLink>
    ),
    expansionMark: true,
  }),
  column({
    label: "Dátum",
    projection: (termin: Termin) => `${termin.datum} ${termin.cas}`,
    sortKey: sortAs.date,
  }),
  column({ label: "Miestnosť", prop: "miestnost", hide: underXS }),
  column({
    label: "Hodnotiaci",
    prop: "hodnotiaci",
    sortKey: sortAs.personName,
    hide: underSM,
  }),
  column({
    label: "Prihlásení",
    sortKey: (termin: Termin) => sortAs.number(termin.pocet_prihlasenych),
    hide: underXS,
    display: (termin: Termin) => (
      <RelativeLink
        href={{
          modal: "zoznamPrihlasenychNaTermin",
          modalTerminKey: termin.termin_key,
        }}
      >
        {termin.pocet_prihlasenych}
        {termin.maximalne_prihlasenych
          ? "/" + termin.maximalne_prihlasenych
          : null}
      </RelativeLink>
    ),
  }),
  column({ label: "Poznámka", prop: "poznamka", hide: underSM }),
  column({
    label: "Prihlasovanie",
    prop: "prihlasovanie",
    sortKey: sortAs.interval,
    hide: underSM,
  }),
  column({
    label: "Odhlasovanie",
    prop: "odhlasovanie",
    sortKey: sortAs.interval,
    hide: underSM,
  }),
  column({
    label: "Známka",
    sortKey: (termin: Termin) =>
      termin.hodnotenie_terminu || termin.hodnotenie_predmetu,
    display: (termin: Termin) => (
      <React.Fragment>
        {termin.hodnotenie_terminu
          ? termin.hodnotenie_terminu
          : termin.hodnotenie_predmetu
          ? termin.hodnotenie_predmetu + " (nepriradená k termínu)"
          : null}
        <SkuskyRegisterButton termin={termin} />
      </React.Fragment>
    ),
  }),
];

function convertToICAL(terminy: Termin[]) {
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

  var dtstamp = new Date()
    .toISOString()
    .replace(/[-:]/g, "")
    .replace(/\.\d+/, "");

  // VEVENTs
  for (var termin of terminy) {
    if (!somPrihlaseny(termin)) continue;

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
    var hodina_koniec = (parseInt(hodina!) + 4).toString();
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
    // TODO ake vsetky informacie chceme zobrazovat v popise eventu? (zatial su take, ako vo FAJR)
    var desc = [
      "Prihlasovanie: " + termin.prihlasovanie,
      "Odhlasovanie: " + termin.odhlasovanie,
      "Poznámka: " + termin.poznamka,
    ].join("\n");
    lines.push("DESCRIPTION:" + desc);

    lines.push("END:VEVENT");
  }

  // footer
  lines.push("END:VCALENDAR");

  return lines.map((l) => l.replace(/\n/g, "\\n")).join("\r\n");
}

function MojeSkuskyMenuLink(props: {
  active: boolean;
  href: Href;
  label: React.ReactNode;
}) {
  return (
    <Link
      className={classNames("btn", "btn-default", props.active && "active")}
      href={props.href}
    >
      {props.label}
    </Link>
  );
}

function MojeSkuskyMenu() {
  var query = useContext(QueryContext);
  var { action, kalendar, zapisnyListKey } = query;
  return (
    <div className="pull-left">
      <div className="skusky-calendar-menu">
        <div className="btn-group">
          <MojeSkuskyMenuLink
            label="Zoznam"
            href={{ action: "mojeSkusky", kalendar: "0", zapisnyListKey }}
            active={kalendar != "1"}
          />
          <MojeSkuskyMenuLink
            label="Kalendár"
            href={{ action: "mojeSkusky", kalendar: "1", zapisnyListKey }}
            active={kalendar == "1"}
          />
        </div>
      </div>
    </div>
  );
}

interface CalendarEvent {
  id: number;
  title: string;
  start: Date;
  end: Date;
  prihlaseny: boolean;
}

function convertToEvents(terminy: Termin[]): CalendarEvent[] {
  return terminy.map((termin, i) => {
    var miestnostStr = termin.miestnost ? ", " + termin.miestnost : "";
    var cas = termin.datum + " " + termin.cas;
    return {
      id: i,
      title: `${termin.nazov_predmetu} (${termin.cas}${miestnostStr})`,
      start: moment(cas, "DD.MM.YYYY HH:mm").toDate(),
      end: moment(cas, "DD.MM.YYYY HH:mm").add(3, "hours").toDate(),
      prihlaseny: somPrihlaseny(termin),
    };
  });
}

function defaultDate(eventList: CalendarEvent[]) {
  var today = new Date();

  if (eventList.length) {
    var lastExamDate = _.maxBy(eventList, "start")!.start;
    if (lastExamDate < today) return lastExamDate;
  }

  return today;
}

function KalendarUdalosti(props: { eventList: CalendarEvent[] }) {
  const localizer = momentLocalizer(moment);

  return (
    <Calendar
      localizer={localizer}
      events={props.eventList}
      views={["month", "week", "day"]}
      defaultDate={defaultDate(props.eventList)}
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
        event: "Skúška",
      }}
      culture={"sk"}
      eventPropGetter={(event) => ({
        className: event.prihlaseny
          ? "skusky-calendar-registered"
          : "skusky-calendar-unregistered",
      })}
      // remove start and end times (we need only one included in title)
      formats={{
        eventTimeRangeFormat: ({ start, end }, culture, local) => "",
      }}
    />
  );
}

function MojeSkuskyPageContent() {
  var query = useContext(QueryContext);
  var cache = new CacheRequester();
  var zapisnyListKey = query.zapisnyListKey!;
  var kalendar = query.kalendar;

  var vidim = cache.get("get_vidim_terminy_hodnotenia", zapisnyListKey);

  if (!cache.loadedAll) {
    return <Loading requests={cache.missing} />;
  }

  if (!vidim) {
    return <p>Skúšky pre tento zápisný list už nie sú k dispozícii.</p>;
  }

  var terminyPrihlasene = cache.get("get_prihlasene_terminy", zapisnyListKey);
  var terminyVypisane = cache.get("get_vypisane_terminy", zapisnyListKey);

  if (!terminyPrihlasene || !terminyVypisane) {
    return <Loading requests={cache.missing} />;
  }

  var terminMap: Record<string, Termin> = {};
  for (const termin of terminyVypisane) terminMap[termin.termin_key] = termin;
  for (const termin of terminyPrihlasene) terminMap[termin.termin_key] = termin;
  var terminy = _.values(terminMap);

  var message = terminy.length
    ? null
    : "Zatiaľ nie sú vypísané žiadne termíny.";

  function handleClickICal() {
    var icalText = convertToICAL(terminyPrihlasene!);
    var blob = new Blob([icalText], { type: "text/calendar;charset=utf-8" });
    saveAs(blob, "MojeTerminy.ics", true);
  }

  return (
    <React.Fragment>
      {kalendar == "1" ? (
        <KalendarUdalosti eventList={convertToEvents(terminy)} />
      ) : (
        <SortableTable
          items={terminy}
          columns={MojeSkuskyColumns}
          queryKey="skuskySort"
          withButtons={true}
          message={message}
          expandedContentOffset={1}
        />
      )}
      {!!terminy.length && (
        <button type="button" onClick={handleClickICal} className="btn">
          Stiahnuť ako iCal
        </button>
      )}
    </React.Fragment>
  );
}

function SkuskyRegisterButton({ termin }: { termin: Termin }) {
  var [pressed, setPressed] = useState(false);

  var isSigninButton = !somPrihlaseny(termin);
  var appearDisabled =
    (isSigninButton && termin.moznost_prihlasit !== "A") || pressed;

  function handleClick() {
    function callback(message: string | null) {
      if (message) {
        setPressed(false);
        alert(message);
      } else {
        invalidateRequestCache("get_prihlasene_terminy");
        invalidateRequestCache("get_vypisane_terminy");
        invalidateRequestCache("get_prihlaseni_studenti");
      }
    }

    if (isSigninButton) {
      sendRpc("prihlas_na_termin", [termin.termin_key], callback);
    } else {
      sendRpc("odhlas_z_terminu", [termin.termin_key], callback);
    }

    setPressed(true);
  }

  if (termin.hodnotenie_terminu) {
    return null;
  }

  var today = new Date().toJSON().replace(/-/g, "").substring(0, 8);
  if (today > sortAs.date(termin.datum)) return null;

  return (
    <button
      type="button"
      onClick={pressed ? undefined : handleClick}
      className={classNames(
        "btn",
        "btn-xs",
        isSigninButton ? "btn-success" : "btn-danger",
        appearDisabled && "appear-disabled"
      )}
    >
      {pressed ? <Loading /> : isSigninButton ? "Prihlásiť" : "Odhlásiť"}
    </button>
  );
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
