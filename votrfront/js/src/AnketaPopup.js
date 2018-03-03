import React, { Component } from 'react';
import { CacheRequester, Loading } from './ajax';

const dropCookie = true; // false disables the Cookie, allowing you to style the banner
const cookieDurationClose = 3;
const cookieDurationVote = 60;
const cookieName = 'anketaKolacik'; // Name of our cookie
const cookieValue = 'on'; // Value of cookie
const cookieHideDate = Date.parse('19 February 2018'); // Starting this day the cookie won't be visible

const createCookie = (name, value, days) => {
  let expires = '';
  if (days) {
    const date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    const expires = '; expires=' + date.toGMTString();
  }
  if (dropCookie) {
    document.cookie = name + '=' + value + expires + '; path=/';
  }
};

const checkCookie = (name) => {
  const nameEQ = name + '=';
  const ca = document.cookie.split(';');
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) === ' ') {
      c = c.substring(1, c.length);
    }
    if (c.indexOf(nameEQ) === 0) {
      return c.substring(nameEQ.length, c.length);
    };
  }
  return null;
};

const eraseCookie = (name) => {
  createCookie(name, '', -1);
};

export class AnketaPopup extends Component {

  componentWillMount() {
    const today = new Date();
    const showPopup = (checkCookie(cookieName) !== cookieValue) && (cookieHideDate > today);

    this.setState({ showPopup });
  }

  onClosePopup(action) {
    if (action === 0) {
      createCookie(cookieName, cookieValue, cookieDurationVote); // Create vote cookie
    } else {
      createCookie(cookieName, cookieValue, cookieDurationClose); // Create close cookie
    }
    this.setState({ showPopup: false });
  }

  render() {
    if (!this.state.showPopup) return null;

    const cache = new CacheRequester();
    const studia = cache.get('get_studia');
    if (!studia) return <div className="hidden"><Loading requests={cache.missing} /></div>;
    if (!studia.some((s) => s.organizacna_jednotka === 'FMFI')) return null;

    return (
      <div className="anketa__wrap">
        <div className="anketa__container">
          <div className="anketa__text-block">
            <img src="http://svt.virpo.sk/smile.svg" className="anketa__image" />
            <div className="anketa__subtitle">
              Daj semestru ešte chvíľu
            </div>
          </div>
          <div className="anketa__button-wrap">
            <a
              className="anketa__button anketa__button--main"
              onClick={() => this.onClosePopup(0)}
              href="https://anketa.fmph.uniba.sk/?anketaPopup"
              target="_blank"
              rel="noopener noreferrer"
            >
              Hlasuj v ankete
            </a>
            <a
              className="anketa__button anketa__button--secondary"
              onClick={() => this.onClosePopup(1)}
              href={(e) => e.preventDefault()}
            >
              Neskôr
            </a>
          </div>
        </div>
      </div>
    );
  }
}
