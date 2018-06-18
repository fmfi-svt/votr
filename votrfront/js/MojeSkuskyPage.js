
import { ZapisnyListSelector } from './ZapisnyListSelector';
import { CacheRequester, Loading, RequestCache, sendRpc } from './ajax';
import { PageLayout, PageTitle } from './layout';
import { Link, queryConsumer } from './router';
import { sortAs, sortTable } from './sorting';
import BigCalendar from 'react-big-calendar';
import moment from 'moment';


// TODO: Oddelit Aktualne terminy hodnotenia vs Stare terminy hodnotenia

export var MojeSkuskyColumns = [
  ["Moje?", null, (termin) => !termin.datum_prihlasenia || termin.datum_odhlasenia ? 'N' : 'A'],
  ["Predmet", 'nazov_predmetu'],
  ["Dátum", 'datum', sortAs.date],
  ["Čas", 'cas'],
  ["Miestnosť", 'miestnost'],
  ["Hodnotiaci", 'hodnotiaci', sortAs.personName],
  ["Prihlásení", 'pocet_prihlasenych', sortAs.number],
  ["Poznámka", 'poznamka'],
  ["Prihlasovanie", 'prihlasovanie', sortAs.interval],
  ["Odhlasovanie", 'odhlasovanie', sortAs.interval],
  ["Známka", null, (termin) => termin.hodnotenie_terminu || termin.hodnotenie_predmetu]
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

function ZobrazenieLink(props) {
  return (<Link className={"btn btn-default" + (props.active ? " active" : "")} href={props.href}>{props.label}</Link>);
}

export function MojeSkuskyMenu(props) {
  var {action, cast, zapisnyListKey} = props.query;
  return (
    <div className="header">
      <div className="pull-right">
        <div className="btn-group">
          <ZobrazenieLink
            label="Zoznam"
            href={{ action: 'mojeSkusky', cast: 'ZZ', zapisnyListKey }}
            active={action == 'mojeSkusky' && cast != 'CA'}
          />
          <ZobrazenieLink
            label="Kalendár"
            href={{ action: 'mojeSkusky', cast: 'CA', zapisnyListKey }}
            active={action == 'mojeSkusky' && cast == 'CA'}
          />
        </div>
      </div>
    </div>
  );
}
MojeSkuskyMenu.propTypes = {
  query: PropTypes.object.isRequired
};

BigCalendar.momentLocalizer(moment); // or globalizeLocalizer

function convertToEvents(terminy){
  let events = [];
  let i = 0;
  for (let termin of terminy){
    events.push({
      id: i,
      title: termin.nazov_predmetu+" ("+termin.cas+", "+termin.miestnost+")",
      startDate: moment(termin.datum+" "+termin.cas, 'DD.MM.YYYY HH:mm').toDate(),
      endDate: moment(termin.datum+" "+termin.cas, 'DD.MM.YYYY HH:mm').add(3,"hours").toDate(),
      prihlaseny: termin.datum_prihlasenia && !termin.datum_odhlasenia,
      vikend: moment(termin.datum+" "+termin.cas, 'DD.MM.YYYY HH:mm').day() >=5
    });
    i += 1;
  }
  return events;
}

export class KalendarUdalosti extends React.Component {
  constructor(props) {
    super(props);
    this.state = {eventList: (props && props.eventList)?props.eventList:[]};
  }
  render(){
    return (
      <BigCalendar
        events={this.state.eventList}
        startAccessor='startDate'
        endAccessor='endDate'
        views={["month", "week", "day"]}
        defaultDate = {new Date()}
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
          (event, start, end, isSelected) => {
            let newStyle = {
              backgroundColor: event.prihlaseny? "#D9534F":"#5CB85C",
            };
            return {
              style: newStyle
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
}

export function MojeSkuskyPageContent() {
  return queryConsumer(query => {
    var cache = new CacheRequester();
    var {zapisnyListKey, cast} = query;

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

    var [terminy, header] = sortTable(
      terminy, MojeSkuskyColumns, query, 'skuskySort');

    var message = terminy.length ? null : "Zatiaľ nie sú vypísané žiadne termíny.";

    function handleClickICal() {
      var icalText = convertToICAL(terminyPrihlasene);
      var blob = new Blob([icalText], {type: "text/calendar;charset=utf-8"});
      saveAs(blob, "MojeTerminy.ics", true);
    }

    return <React.Fragment>
      <MojeSkuskyMenu query={query} />
      {cast === "CA"?
        <div style={{height:"90vh"}}>
          <KalendarUdalosti eventList={convertToEvents(terminy)}/>
        </div>
        : null
      }
      {cast !== "CA"?
        <table className="table table-condensed table-bordered table-striped table-hover with-buttons-table">
          <thead>{header}</thead>
          <tbody>
            {terminy.map((termin) =>
              <tr key={termin.termin_key}>
                {!termin.datum_prihlasenia || termin.datum_odhlasenia ?
                  <td title="Nie ste prihlásení" className="text-center text-negative">{"\u2718"}</td> :
                  <td title="Ste prihlásení" className="text-center text-positive">{"\u2714"}</td> }
                <td><Link href={{ ...query, modal: 'detailPredmetu', modalPredmetKey: termin.predmet_key, modalAkademickyRok: termin.akademicky_rok }}>
                  {termin.nazov_predmetu}
                </Link></td>
                <td>{termin.datum}</td>
                <td>{termin.cas}</td>
                <td>{termin.miestnost}</td>
                <td>{termin.hodnotiaci}</td>
                <td><Link href={{ ...query, modal: 'zoznamPrihlasenychNaTermin', modalTerminKey: termin.termin_key }}>
                  {termin.pocet_prihlasenych +
                   (termin.maximalne_prihlasenych ? "/" + termin.maximalne_prihlasenych : "")}
                </Link></td>
                <td>{termin.poznamka}</td>
                <td>{termin.prihlasovanie}</td>
                <td>{termin.odhlasovanie}</td>
                <td>
                  {termin.hodnotenie_terminu ? termin.hodnotenie_terminu :
                   termin.hodnotenie_predmetu ? termin.hodnotenie_predmetu + ' (nepriradená k termínu)' :
                   null}
                   <SkuskyRegisterButton termin={termin}/>
                </td>
              </tr>
            )}
          </tbody>
          {message && <tfoot><tr><td colSpan={MojeSkuskyColumns.length}>{message}</td></tr></tfoot>}
        </table>
        : null
      }
      {terminy.length && <button onClick={handleClickICal} className="btn">Stiahnuť ako iCal</button>}
    </React.Fragment>;
  });
}


export class SkuskyRegisterButton extends React.Component {
  static propTypes = {
    termin: PropTypes.object.isRequired
  };

  state = {
    pressed: false
  }

  handleClick = () => {
    var command = this.isSigninButton() ? 'prihlas_na_termin' : 'odhlas_z_terminu';
    var termin = this.props.termin;

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

  isDisabled() {
    var termin = this.props.termin;
    return (this.isSigninButton() && termin.moznost_prihlasit !== 'A') || this.state.pressed;
  }

  isSigninButton() {
    var termin = this.props.termin;
    return !termin.datum_prihlasenia || termin.datum_odhlasenia;
  }

  render() {
    var termin = this.props.termin;

    if (termin.hodnotenie_terminu) {
      return null;
    }

    var today = new Date().toJSON().replace(/-/g, '').substring(0, 8);
    if (today > sortAs.date(termin.datum)) return null;

    var buttonClass = "btn btn-xs " + (this.isSigninButton() ? "btn-success" : "btn-danger") + (this.isDisabled() ? " appear-disabled" : "");
    var buttonText = this.state.pressed ? <Loading /> : this.isSigninButton() ? "Prihlásiť" : "Odhlásiť";

    return <button onClick={this.state.pressed ? null : this.handleClick} className={buttonClass}>{buttonText}</button>;
  }
}


export function MojeSkuskyPage() {
  return (
    <PageLayout>
      <ZapisnyListSelector>
        <div className="header">
          <PageTitle>Moje skúšky</PageTitle>
        </div>
        <MojeSkuskyPageContent />
      </ZapisnyListSelector>
    </PageLayout>
  );
}
