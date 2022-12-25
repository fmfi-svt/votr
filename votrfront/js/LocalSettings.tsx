export var LocalSettings = {
  get(key: string): string | null {
    return localStorage.getItem(Votr.settings.instance_name + "_" + key);
  },

  set(key: string, value: string) {
    localStorage.setItem(Votr.settings.instance_name + "_" + key, value);
    Votr.updateRoot();
  },
};
