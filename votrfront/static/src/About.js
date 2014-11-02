/** @jsx React.DOM */

(function () {


Votr.AboutModal = React.createClass({
  render: function () {
    return <Votr.Modal title="O aplikácii">
      <p>
        Len málokto sa vyzná v AISe. Kým sa študent dostane k tomu, čo
        potrebuje, musí sa prebiť cez hŕbu okien a menu. A ani pravidelné
        činnosti, ako zapisovanie na skúšky, nie sú výnimkou. Preto sme spravili
        Votr. Vybrali sme tie najdôležitejšie informácie z AISu a sprístupnili
        sme ich na jeden klik.
      </p>
      <p>
        Cez Votr si študenti môžu zapísať skúšky, pozrieť hodnotenia,
        skontrolovať počet kreditov a podobne. Votr používa tie isté dáta, ako
        AIS2, ale podáva ich prehľadnejším spôsobom.
      </p>
      <h3>Pomoc a technická podpora</h3>
      <p>
        Votr je nová aplikácia a môžu sa v nej vyskytnúť chyby. Ak vám
        Votr nefunguje, ospravedlňujeme sa! Zavolajte na <a
        href="http://staryweb.uniba.sk/cepit" target="_blank">hotline CePIT</a>,
        kde môžete nahlásiť problémy, navrhnúť vylepšenia a dostať pomoc s
        používaním Votru.
      </p>
      <p>
        Cez Votr sa nedá robiť všetko to, čo v AIS2 &mdash; sústredí sa na
        zjednodušenie tých najčastejších činností. Ak hľadáte záverečné práce,
        štátne skúšky a ďalšie menej časté veci, musíte ísť cez AIS2.
      </p>
      <h3>Autori projektu</h3>
      <p>
        Votr je projektom Študentského vývojového tímu z Fakulty matematiky,
        fyziky a informatiky UK. Naprogramovali ho Tomáš Belan, Dušan Plavák a
        Kristián Valentín. Napíšte nám na <a
        href="mailto:votr-devel@googlegroups.com"
        >votr-devel@googlegroups.com</a>.
      </p>
      <p>
        Votr je aplikácia s otvoreným zdrojovým kódom. Vývoj prebieha verejne
        a na <a href="https://github.com/fmfi-svt/votr" target="_blank">stránke
        projektu</a> môžete sledovať, na čom práve pracujeme. Ak sa vám Votr
        páči a chceli by ste sa zapojiť, napíšte nám!
      </p>
    </Votr.Modal>;
  }
});


})();
