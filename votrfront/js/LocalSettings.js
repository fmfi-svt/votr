
import { settings } from './settings';

export var LocalSettings = {
  get(key) {
    return localStorage.getItem(settings.instance_name + "_" + key);
  },

  set(key, value) {
    localStorage.setItem(settings.instance_name + "_" + key, value);
    Votr.appRoot.forceUpdate();
  }
};
