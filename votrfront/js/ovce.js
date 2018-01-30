var dropCookie = true;                      // false disables the Cookie, allowing you to style the banner
var cookieDurationClose = 3;
var cookieDurationVote = 60;
var cookieName = 'ovcaKolacik';        // Name of our cookie
var cookieValue = 'on';                     // Value of cookie
 
function createDiv(){
    var bodytag = document.getElementsByTagName('body')[0];
    var div = document.createElement('div');
    div.setAttribute('id','cookie-ovca');

    div.innerHTML = '<link href="https://fonts.googleapis.com/css?family=Open+Sans:300,400,700&amp;subset=latin-ext" rel="stylesheet"><div class="anketa__wrap"><div class="anketa__container"><div class="anketa__text-block"><img src="http://svt.virpo.sk/smile.svg" class="anketa__image"><div class="anketa__subtitle">Daj semestru ešte chvíľu</div></div><div class="anketa__button-wrap"><a class="anketa__button anketa__button--main" href="https://anketa.fmph.uniba.sk/?anketaPopup" target="_blank" rel="noopener noreferrer" onclick="removeMe(0);">Hlasuj v ankete</a><a class="anketa__button anketa__button--secondary" href="javascript:void(0);" onclick="removeMe(1);">Neskôr</a></div></div></div>';
     
    bodytag.insertBefore(div,bodytag.firstChild); // Adds the Cookie Law Banner just after the opening <body> tag
     
    document.getElementsByTagName('body')[0].className+=' cookiebanner'; //Adds a class tothe <body> tag when the banner is visible
}
 
 
function createCookie(name,value,days) {
    if (days) {
        var date = new Date();
        date.setTime(date.getTime()+(days*24*60*60*1000)); 
        var expires = "; expires="+date.toGMTString(); 
    }
    else var expires = "";
    if(window.dropCookie) { 
        document.cookie = name+"="+value+expires+"; path=/"; 
    }
}
 
function checkCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1,c.length);
        console.log(c.indexOf(nameEQ));
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
}
 
function eraseCookie(name) {
    createCookie(name,"",-1);
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
 
window.onload = function(){
    if (checkCookie(window.cookieName) != window.cookieValue) {
        isFromFMFI(createDiv);
    }
}

function removeMe(action){
    var element = document.getElementById('cookie-ovca');
    element.parentNode.removeChild(element);
    if(action == 0) {
      createCookie(window.cookieName,window.cookieValue, window.cookieDurationVote); // Create vote the cookie
    } else {
      createCookie(window.cookieName,window.cookieValue, window.cookieDurationClose); // Create close the cookie
    }
}
