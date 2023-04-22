export function getLocalSetting(key: string): string | null {
  return localStorage.getItem(Votr.settings.instance_id + "_" + key);
}

export function setLocalSetting(key: string, value: string) {
  localStorage.setItem(Votr.settings.instance_id + "_" + key, value);
  Votr.updateRoot();
}
