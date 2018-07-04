
import { CacheRequester, Loading } from './ajax';

var dropCookie = true;  // false disables the Cookie, allowing you to style the banner
var cookieDurationClose = 3;
var cookieDurationVote = 60;
var cookieName = 'anketaKolacik2018Leto'; // Name of our cookie
var cookieValue = 'on'; // Value of cookie
var cookieHideDate = Date.parse('3 July 2018'); // Starting this day the cookie won't be visible


export class AnketaPopup extends React.Component {
  constructor(props) {
    super(props);
    var today = new Date();
    var showPopup = checkCookie(cookieName) != cookieValue && cookieHideDate > today;
    this.state = { showPopup };
  }

  onClosePopup = (action) => {
    if(action == 0) {
      createCookie(cookieName, cookieValue, cookieDurationVote); // Create vote cookie
    } else {
      createCookie(cookieName, cookieValue, cookieDurationClose); // Create close cookie
    }
    this.setState({showPopup: false})
  }

  render() {
    if (!this.state.showPopup) return null;

    var cache = new CacheRequester();
    var studia = cache.get('get_studia');
    if (!studia) return <div className="hidden"><Loading requests={cache.missing} /></div>;
    if (!studia.some(s => s.organizacna_jednotka == 'FMFI')) return null;

    return <div className="anketa__wrap">
             <div className="anketa__container">
                <div className="anketa__text-block">
                    <img src="http://svt.virpo.sk/smile.svg" className="anketa__image"/>
                        <div className="anketa__subtitle">Daj semestru ešte chvíľu</div>
                </div>
                <div className="anketa__button-wrap">
                    <a className="anketa__button anketa__button--main" onClick={() => {this.onClosePopup(0)}} href="https://anketa.fmph.uniba.sk/?anketaPopup" target="_blank" rel="noopener noreferrer" >Hlasuj v ankete</a>
                    <a className="anketa__button anketa__button--secondary" onClick={() => {this.onClosePopup(1)}} href="javascript:void(0);">Neskôr</a>
                </div>
            </div>
           </div>;
  }
}


function createCookie(name, value, days) {
    if (days) {
        var date = new Date();
        date.setTime(date.getTime()+(days*24*60*60*1000)); 
        var expires = "; expires="+date.toGMTString(); 
    }
    else var expires = "";
    if(dropCookie) { 
        document.cookie = name+"="+value+expires+"; path=/"; 
    }
}
 
function checkCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
}
 
function eraseCookie(name) {
    createCookie(name,"",-1);
}
