
import { Modal, PageLayout } from './layout';


export var AboutModal = createReactClass({
  render() {
    var github = "https://github.com/fmfi-svt/votr";
    return <Modal title="O aplikácii">
      <p>
        Len málokto sa vyzná v AISe. Kým sa študent dostane k tomu, čo
        potrebuje, musí sa prebiť cez hŕbu okien a menu. A ani pravidelné
        činnosti, ako zapisovanie sa na skúšky, nie sú výnimkou. Preto sme
        vytvorili aplikáciu Votr. Vybrali sme tie najdôležitejšie informácie z
        AISu a sprístupnili sme ich na jeden klik.
      </p>
      <p>
        Cez Votr si študenti môžu zapísať skúšky, pozrieť hodnotenia,
        skontrolovať počet kreditov a podobne. Votr používa tie isté dáta, ako
        AIS, ale podáva ich prehľadnejším spôsobom.
      </p>
      <h4>Pomoc a technická podpora</h4>
      <p>
        Ak vám Votr nefunguje alebo máte akékoľvek otázky, nápady či
        pripomienky, napíšte nám na <a href="mailto:fmfi-svt@googlegroups.com">
        fmfi-svt@googlegroups.com</a> a radi vám pomôžeme. Alebo ak chcete,
        môžete zavolať na <a href="https://uniba.sk/cepit" target="_blank">
        hotline CePIT</a>.
      </p>
      <p>
        Cez Votr sa nedá robiť všetko to, čo v AISe &mdash; sústredí sa na
        zjednodušenie tých najčastejších činností. Ak hľadáte záverečné práce,
        štátne skúšky a ďalšie menej časté veci, musíte ísť cez AIS.
      </p>
      <h4>Autori projektu</h4>
      <p>
        Votr je projektom Študentského vývojového tímu z Fakulty matematiky,
        fyziky a informatiky UK. Naprogramovali ho Tomáš Belan, Dušan Plavák <a
        href="https://github.com/fmfi-svt/votr/graphs/contributors"
        target="_blank" rel="nofollow">a ďalší spoluautori</a>. Vývoj prebieha
        verejne na stránke <a href={github} target="_blank">{github}</a>. Ak sa
        vám Votr páči a chceli by ste sa zapojiť, napíšte nám!
      </p>
      <h4>Meno projektu</h4>
      <p>
        Čo znamená meno "Votr"? Je to fonetický prepis anglického slova "water".
        V tejto slovnej hračke začal už predchodca Votru, ktorý sa volal "FAJR"
        (pretože "fajr" a "ais" sú protiklady). Keď sme sa neskôr rozhodli
        prebudovať FAJR na novom základe, nazvali sme ho "Votr", lebo má ku AISu
        bližšie a vie s ním plynule narábať. Aj mená interných súčastí Votru
        pokračujú v tejto téme.
      </p>
    </Modal>;
  }
});


export var IndexPage = createReactClass({
  render() {
    // TODO: Use PageTitle, but show different h1.
    return <PageLayout query={this.props.query}>
      <h1>Vitajte</h1>
      <p>
        Votr je alternatívne rozhranie pre systém AIS2. Cez menu sa dostanete
        k týmto informáciám:
      </p>
      <ul>
        <li><p>
          <strong>Moje predmety</strong> &mdash; predmety, ktoré máte zapísané
          v tomto alebo minulom akademickom roku, a získané hodnotenia
        </p></li>
        <li><p>
          <strong>Moje skúšky</strong> &mdash; termíny skúšok, na ktoré ste
          prihlásení resp. na ktoré sa môžete prihlásiť
        </p></li>
        <li><p>
          <strong>Moje hodnotenia</strong> &mdash; hodnotenia predmetov a
          získané študijné priemery za celé štúdium
        </p></li>
        <li><p>
          <strong>Priebežné hodnotenia</strong> &mdash; priebežné hodnotenia
          predmetov počas semestra
        </p></li>
        <li><p>
          <strong>Zápis predmetov</strong> &mdash; pridávanie a odoberanie
          predmetov zo súčasného zápisného listu
        </p></li>
        <li><p>
          <strong>Prehľad štúdia</strong> &mdash; zoznam vašich štúdií a
          zápisných listov
        </p></li>
        <li><p>
          <strong>Register osôb</strong> &mdash; vyhľadávanie zamestnancov,
          študentov a absolventov univerzity, e-mailové kontakty
        </p></li>
        <li><p>
          <strong>Register predmetov</strong> &mdash; vyhľadávanie predmetov,
          informácie o ich učiteľoch a zoznamy zapísaných študentov
        </p></li>
      </ul>
    </PageLayout>
  }
});
