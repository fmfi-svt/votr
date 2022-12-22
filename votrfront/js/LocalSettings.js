
export var LocalSettings = {
  get(key) {
    return localStorage.getItem(Votr.settings.instance_name + "_" + key);
  },

  set(key, value) {
    localStorage.setItem(Votr.settings.instance_name + "_" + key, value);
    Votr.updateRoot();
  }
};
