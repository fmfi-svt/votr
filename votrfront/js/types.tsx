export interface VotrServer {
  title: string;
  login_types: string[];
  ais_cookie?: string;
  rest_cookie?: string;
}

export interface VotrVar {
  settings: {
    url_root: string;
    instance_name: string;
    anketa_season?: string;
    anketa_end_msec?: number;
    servers?: VotrServer[];
    invalid_session?: boolean;
    error?: string;
    csrf_token?: string | null;
    server?: number;
    type?: string | null;
    destination?: string | undefined;
  };
  updateRoot(): void;
  ajaxError: string | null;
  [key: string]: unknown;
}

export type Query = Record<string, string>;

export type Href = Record<string, string | null | undefined>;

// Fladgejt structures

export interface Studium {
  sp_skratka: string;
  sp_popis: string;
  sp_doplnujuce_udaje: string;
  zaciatok: string;
  koniec: string;
  sp_dlzka: string;
  sp_cislo: string;
  rok_studia: string;
  organizacna_jednotka: string;
  studium_key: string;
}

export interface ZapisnyList {
  akademicky_rok: string;
  rocnik: string;
  sp_skratka: string;
  sp_popis: string;
  datum_zapisu: string;
  studium_key: string;
  zapisny_list_key: string;
}

export interface Predmet {
  skratka: string;
  nazov: string;
  typ_vyucby: string;
  semester: string;
  kredit: string;
  predmet_key: string;
}

export interface RegPredmet {
  skratka: string;
  nazov: string;
  konanie: string;
  stredisko: string;
  fakulta: string;
  cudzi_nazov: string;
  rozsah_vyucby: string;
  semester: string;
  kredit: string;
  predmet_key: string;
}

export interface ZapisPredmet {
  skratka: string;
  nazov: string;
  typ_vyucby: string;
  semester: string;
  kredit: string;
  rozsah_vyucby: string;
  jazyk: string;
  datum_zapisu: string | null;
  aktualnost: string;
  pocet_prihlasenych: string | null;
  maximalne_prihlasenych: string | null;
  blok_skratka: string | null;
  blok_nazov: string | null;
  blok_index: string | null;
  v_bloku_index: string | null;
  odporucany_rocnik: string | null;
  cast: string;
  predmet_key: string;
}

export interface ZapisVlastnost {
  skratka: string;
  nazov: string;
  minimalny_kredit: string;
  poznamka: string;
}

export interface Hodnotenie {
  akademicky_rok: string;
  skratka: string;
  nazov: string;
  typ_vyucby: string;
  semester: string;
  kredit: string;
  hodn_znamka: string;
  hodn_termin: string;
  hodn_datum: string;
  hodn_znamka_popis: string;
  zapisny_list_key: string;
  predmet_key: string;
  hodn_key: string;
}

export interface PriebezneHodnotenie {
  dovod: string;
  poc_bodov: string;
  maximum: string;
  zaevidoval: string;
  zapocitavat: string;
  minimum: string;
}

export interface PriebezneHodnoteniaPredmetu {
  akademicky_rok: string;
  skratka: string;
  nazov: string;
  semester: string;
  kredit: string;
  zaznamy: PriebezneHodnotenie[];
  predmet_key: string;
}

export interface Priemer {
  akademicky_rok: string;
  nazov: string;
  semester: string;
  ziskany_kredit: string;
  predmetov: string;
  neabsolvovanych: string;
  studijny_priemer: string;
  vazeny_priemer: string;
  pokusy_priemer: string;
  datum_vypoctu: string;
}

export interface Termin {
  datum: string;
  cas: string;
  miestnost: string;
  pocet_prihlasenych: string;
  maximalne_prihlasenych: string;
  hodnotiaci: string;
  prihlasovanie: string;
  odhlasovanie: string;
  poznamka: string;
  akademicky_rok: string;
  nazov_predmetu: string;
  skratka_predmetu: string;
  moznost_prihlasit: string;
  datum_prihlasenia: string;
  datum_odhlasenia: string;
  hodnotenie_terminu: string;
  hodnotenie_predmetu: string;
  zapisny_list_key: string;
  predmet_key: string;
  termin_key: string;
}

export interface PrihlasenyStudent {
  sp_skratka: string;
  datum_prihlasenia: string;
  plne_meno: string;
  rocnik: string;
  email: string;
}

export interface Obdobie {
  obdobie_od: string;
  obdobie_do: string;
  id_akcie: string;
}

export interface RegUcitelPredmetu {
  plne_meno: string;
  typ: string;
}

export interface RegOsoba {
  meno: string;
  priezvisko: string;
  plne_meno: string;
  email: string;
}

export interface ComboBoxOption {
  title: string;
  id: string;
  tool_tip_text?: String;
}

export type ZapisCast = "SC" | "SS";

export interface Rpcs {
  // hodnotenia.py
  get_hodnotenia(
    zapisny_list_key: string
  ): [items: Hodnotenie[], message: string | null];
  get_priemery(
    zapisny_list_key: string
  ): [items: Priemer[], message: string | null];
  get_priebezne_hodnotenia(
    zapisny_list_key: string
  ): [items: PriebezneHodnoteniaPredmetu[], message: string | null];

  // obdobia.py
  get_semester_obdobie(semester: "Z" | "L", akademicky_rok?: string): Obdobie;
  get_skuskove_obdobie(semester: "Z" | "L", akademicky_rok?: string): Obdobie;

  // osoby.py
  vyhladaj_osobu(
    meno: string,
    priezvisko: string,
    absolvent: boolean,
    student: boolean,
    zamestnanec: boolean,
    akademicky_rok: string,
    fakulta: string,
    studijny_program: string,
    uchadzaci: boolean,
    prvy_rocnik: boolean,
    druhy_rocnik: boolean,
    treti_rocnik: boolean,
    stvrty_rocnik: boolean,
    piaty_rocnik: boolean,
    siesty_rocnik: boolean,
    siedmy_rocnik: boolean,
    osmy_rocnik: boolean,
    absolventi: boolean
  ): [items: RegOsoba[], message: string | null];
  get_register_osob_akademicky_rok_options(): ComboBoxOption[];
  get_register_osob_fakulty(): ComboBoxOption[];

  // predmety.py
  get_informacny_list(
    kod_predmetu: string,
    akademicky_rok: string
  ): string | null;
  get_studenti_zapisani_na_predmet(
    predmet_key: string,
    akademicky_rok: string
  ): [studenti: PrihlasenyStudent[], predmet: RegPredmet | null];
  get_ucitelia_predmetu(
    predmet_key: string,
    akademicky_rok: string,
    semester: string,
    fakulty: string
  ): RegUcitelPredmetu[];
  vyhladaj_predmety(
    akademicky_rok: string,
    fakulta: string | null,
    stredisko: string | null,
    skratka_sp: string | null,
    skratka_predmetu: string | null,
    nazov_predmetu: string | null,
    semester: string | null,
    stupen: string | null
  ): [items: RegPredmet[], message: string | null];
  get_register_predmetov_fakulta_options(): ComboBoxOption[];
  get_register_predmetov_akademicky_rok_options(): ComboBoxOption[];
  get_register_predmetov_semester_options(): ComboBoxOption[];
  get_register_predmetov_stupen_options(): ComboBoxOption[];

  // studium.py
  get_som_student(): boolean;
  get_studia(): Studium[];
  get_zapisne_listy(studium_key: string): ZapisnyList[];
  zapisny_list_key_to_akademicky_rok(zapisny_list_key: string): string;
  get_prehlad_kreditov(
    studium_key: string
  ): [items: Hodnotenie[], message: string | null];
  get_akademicke_roky_noveho_zapisneho_listu(
    studium_key: string
  ): ComboBoxOption[];
  get_roky_studia_noveho_zapisneho_listu(studium_key: string): ComboBoxOption[];
  create_zapisny_list(
    studium_key: string,
    akademicky_rok: string,
    rok_studia: string | null
  ): string | null;
  delete_zapisny_list(zapisny_list_key: string): null;

  // terminy.py
  get_vidim_terminy_hodnotenia(zapisny_list_key: string): boolean;
  get_predmety(zapisny_list_key: string): Predmet[];
  get_prihlasene_terminy(zapisny_list_key: string): Termin[];
  get_vypisane_terminy(zapisny_list_key: string): Termin[];
  get_vypisane_terminy_predmetu(
    zapisny_list_key: string,
    predmet_key: string
  ): Termin[];
  get_prihlaseni_studenti(termin_key: string): PrihlasenyStudent[];
  prihlas_na_termin(termin_key: string): string | null;
  odhlas_z_terminu(termin_key: string): string | null;

  // zapis.py
  zapis_get_zapisane_predmety(
    zapisny_list_key: string,
    cast: ZapisCast
  ): [items: ZapisPredmet[], message: string | null];
  zapis_get_vlastnosti_programu(
    zapisny_list_key: string
  ): [items: ZapisVlastnost[], message: string | null];
  zapis_plan_vyhladaj(
    zapisny_list_key: string,
    cast: ZapisCast
  ): [items: ZapisPredmet[], message: string | null];
  zapis_plan_pridaj_predmety(
    zapisny_list_key: string,
    cast: ZapisCast,
    dvojice_typ_vyucby_skratka: [string, string][]
  ): string | null;
  zapis_ponuka_vyhladaj(
    zapisny_list_key: string,
    fakulta: string | null,
    stredisko: string | null,
    filter_skratka: string | null,
    filter_nazov: string | null
  ): [items: ZapisPredmet[], message: string | null];
  zapis_ponuka_pridaj_predmety(
    zapisny_list_key: string,
    fakulta: string | null,
    stredisko: string | null,
    filter_skratka: string | null,
    filter_nazov: string | null,
    zvolene_skratky: string[]
  ): string | null;
  zapis_ponuka_options(
    zapisny_list_key: string
  ): [items: ComboBoxOption[], message: string | null];
  zapis_odstran_predmety(
    zapisny_list_key: string,
    cast: ZapisCast,
    predmet_key_list: string[]
  ): string | null;
}

export interface Columns extends Array<any> {
  defaultOrder?: string;
}
