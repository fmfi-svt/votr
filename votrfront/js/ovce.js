var cookieDurationClose = 3;
var cookieDurationVote = 60;
var cookieName = 'ovcaKolacik'; // Name of our cookie
var cookieValue = 'on'; // Value of cookie
var cookieHideDate = Date.parse('6 Jul 2017'); // Starting this day the cookie won't be visible

function createDiv() {
  var bodytag = document.getElementsByTagName('body')[0];
  var div = document.createElement('div');
  div.setAttribute('id', 'cookie-ovca');
  div.innerHTML = '<style>.ovca__wrap{background-color: white;font-family: "Open Sans";font-size: 15px;border: 1px solid #c5c5c5;border-left: 0;position: absolute;left: -200px;top: 235px;animation: slide 0.5s forwards;animation-delay: 2s;border-top-right-radius: 3px;border-bottom-right-radius: 3px;z-index: 99999;}.ovca__container{padding: 10px 15px 15px 15px;position: relative;display: flex;flex-direction: column;align-items: center;width: 180px;}.ovca__image{position: absolute;top: 50px;left: 20px;animation: flySheepFly 1.25s linear infinite;}.ovca__button-wrap{margin-top: 125px;text-align: center;display: flex;flex-direction: column;}.ovca__button{border: 1px solid #b51b1b;padding: 3px 15px;border-radius: 3px;background-color: #cd2a2a;text-decoration: none;color: white;}.ovca__button--red{border-color: #b51b1b;background-color: #cd2a2a;color: white;}.ovca__button--red:hover{color: white;}.ovca__button--white{border-color: #c5c5c5;background-color: white;color: black;margin-top: 5px;}@keyframes flySheepFly {0% {margin-top: 0.25em;transform: rotate(-4deg);}33% {transform: rotate(4deg);margin-top: -0.25em;}67% {transform: rotate(-6deg);margin-top: -0.125em;}100% {transform: rotate(-4deg);margin-top: 0.25em;}}@keyframes slide {100% { left: 0; }}@media (max-width: 767px){.ovca__wrap{top: 15px;}}</style>';
  div.innerHTML += '<link href="https://fonts.googleapis.com/css?family=Open+Sans&amp;subset=latin-ext" rel="stylesheet"><div class="ovca__wrap"><div class="ovca__container"><div class="ovca__text">Nebuď ovca!</div><a href="https://anketa.fmph.uniba.sk/?ovcaImage" target="_blank" rel="noopener noreferrer" onclick="removeMe(window.cookieDurationVote);"><img src="https://i.imgur.com/7YWj2E6.png" alt="Lietajuca ovecka" class="ovca__image" /></a><div class="ovca__button-wrap"><a class="ovca__button ovca__button--red" href="https://anketa.fmph.uniba.sk/?ovca" target="_blank" rel="noopener noreferrer" onclick="removeMe(window.cookieDurationVote);">Hlasuj v ankete!</a><a class="ovca__button ovca__button--white" href="javascript:void(0);" onclick="removeMe(window.cookieDurationClose);">Zatvor</a></div></div></div>';

  bodytag.insertBefore(div, bodytag.firstChild); // Adds the Cookie Law Banner just after the opening <body> tag

  document.getElementsByTagName('body')[0].className += ' cookiebanner'; //Adds a class tothe <body> tag when the banner is visible
}


function createCookie(name, value, days) {
  if (days) {
    var date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    var expires = "; expires=" + date.toGMTString();
  }
  else var expires = "";
  document.cookie = name + "=" + value + expires + "; path=/";
}

function checkCookie(name) {
  var nameEQ = name + "=";
  var ca = document.cookie.split(';');
  for (var i = 0; i < ca.length; i++) {
    var c = ca[i];
    while (c.charAt(0) == ' ') c = c.substring(1, c.length);
    if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length, c.length);
  }
  return null;
}

function eraseCookie(name) {
  createCookie(name, "", -1);
}

function removeMe(duration) {
  var element = document.getElementById('cookie-ovca');
  element.parentNode.removeChild(element);
  createCookie(window.cookieName, window.cookieValue, duration);
}

function isFromFMFI(callback) {
  $.ajax({
    "type": "POST",
    "url": '/rpc?name=get_studia',
    data: "[]",
    success: function (msg) {
      if(msg.match(/"organizacna_jednotka": "FMFI"/) != null) {
        callback();
      }
    },
    beforeSend: function (req) {
      req.setRequestHeader('X-CSRF-Token', Votr.settings.csrf_token);
      req.setRequestHeader('Content-Type', 'application/json')
    }
  })
}

function checkDOMChange() {
  if ($('.main-menu li').size() >= 11) {
    var today = new Date();
    if ((checkCookie(window.cookieName) != window.cookieValue) && (cookieHideDate > today)) {
      isFromFMFI(createDiv);
    }
  } else {
    setTimeout(checkDOMChange, 100);
  }
}

$(document).ready(function () {
  checkDOMChange();
});
