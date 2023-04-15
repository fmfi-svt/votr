import React from "react";
import { CacheRequester, Loading } from "./ajax";
import { getLocalSetting, setLocalSetting } from "./LocalSettings";

export function AnketaPopup() {
  const season = Votr.settings.anketa_season;

  if (!season) return null;

  if (Date.now() > Votr.settings.anketa_end_msec!) return null;

  let wasClosedBefore = false;

  try {
    const state = getLocalSetting("anketapopup");
    if (state) {
      const [savedSeason, savedTime] = JSON.parse(state) as [string, number];
      if (savedSeason == season) {
        if (savedTime == -1 || Date.now() < savedTime) {
          return null;
        }
        wasClosedBefore = true;
      }
    }
  } catch (e) {
    // Ignore the error. Proceed with wasClosedBefore = false.
  }

  const cache = new CacheRequester();
  const studia = cache.get("get_studia");
  if (!studia) {
    return (
      <div className="hidden">
        <Loading requests={cache.missing} />
      </div>
    );
  }
  if (!studia.some((s) => s.organizacna_jednotka == "FMFI")) return null;

  function closePopup(until: number) {
    setLocalSetting("anketapopup", JSON.stringify([season, until]));
  }

  const later = 3 * 24 * 3600 * 1000;
  const laterText = "Pripomenúť o 3 dni";

  return (
    <div className="anketapopup">
      <button
        type="button"
        className="close"
        onClick={() => closePopup(Date.now() + later)}
        aria-label="Zavrieť"
      >
        <span aria-hidden="true">&times;</span>
      </button>
      <div className="anketapopup-line1">Daj semestru ešte chvíľu</div>
      <div className="anketapopup-line2">
        <strong>Hlasuj v ankete</strong>
      </div>
      <div className="anketapopup-buttons">
        <a
          className="btn btn-primary"
          onClick={() => closePopup(-1)}
          href="https://anketa.fmph.uniba.sk/?anketaPopup"
          target="_blank"
          rel="noopener noreferrer"
        >
          Otvoriť anketu
        </a>
        <button
          type="button"
          className="btn btn-default"
          onClick={() => closePopup(Date.now() + later)}
          title={laterText}
        >
          Neskôr
        </button>
        {wasClosedBefore && (
          <button
            type="button"
            className="btn btn-default"
            onClick={() => closePopup(-1)}
            title="Už nepripomínať"
          >
            Stop
          </button>
        )}
      </div>
    </div>
  );
}
