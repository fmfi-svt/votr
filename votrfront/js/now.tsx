export function getMsecNow() {
  // eslint-disable-next-line no-restricted-syntax
  return Votr.settings.fake_time_msec || Date.now();
}

export function getDateNow() {
  return new Date(getMsecNow());
}
