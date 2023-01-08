import { reportClientError } from "./ajax";

const fallback = new Map<string, string>();

let me: number | undefined;

function tryGet(fn: () => unknown) {
  try {
    return String(fn());
  } catch (e) {
    return "failed: " + e;
  }
}

function reportLocalStorageError(subtype: string, e: unknown) {
  // Our logs indicate some iPhone users have window.localStorage === null.
  // That's very strange. Let's log more info about the error.
  me = me || Math.random();
  reportClientError("custom", {
    subtype,
    me,
    errorString: "" + e,
    stack: e && (e as { stack: unknown }).stack,
    localStorage: tryGet(() => window.localStorage),
    getItem: tryGet(() => window.localStorage.getItem),
    setItem: tryGet(() => window.localStorage.setItem),
    sessionStorage: tryGet(() => window.sessionStorage),
    closed: tryGet(() => window.closed),
    console: tryGet(() => window.console),
    document: tryGet(() => window.document),
  });
  console.error(e);
}

export function getLocalSetting(key: string): string | null {
  try {
    return localStorage.getItem(Votr.settings.instance_name + "_" + key);
  } catch (e: unknown) {
    reportLocalStorageError("getLocalSetting", e);
    return fallback.get(key) ?? null;
  }
}

export function setLocalSetting(key: string, value: string) {
  fallback.set(key, value);
  try {
    localStorage.setItem(Votr.settings.instance_name + "_" + key, value);
  } catch (e: unknown) {
    reportLocalStorageError("setLocalSetting", e);
  }
  Votr.updateRoot();
}
