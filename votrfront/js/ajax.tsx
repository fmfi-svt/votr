import React, { useEffect } from "react";
import { Rpcs } from "./types";

interface RpcAnnouncementPayload {
  announcement_html: string;
}
interface RpcLogPayload {
  log: string;
  message: string;
  time: number;
}
interface RpcErrorPayload {
  error: string;
}
interface RpcResultPayload {
  result: unknown;
}
type RpcPayload =
  | RpcAnnouncementPayload
  | RpcLogPayload
  | RpcErrorPayload
  | RpcResultPayload;

const HEADER_LENGTH = 10;

interface RpcCall {
  name: string;
  stringifiedArgs: string;
  callback: (result: unknown) => void;
}

function sendRawRpcs(calls: RpcCall[]) {
  let processed = 0;
  let results = 0;
  let finished = false;

  function update() {
    if (finished) return;
    // eslint-disable-next-line no-constant-condition, @typescript-eslint/no-unnecessary-condition
    while (true) {
      if (xhr.status && xhr.status != 200) {
        const error =
          `Network error: HTTP ${xhr.status}` +
          (xhr.statusText ? ": " + xhr.statusText : "");
        fail(error, {
          subtype: "status",
          responseText: xhr.responseText,
          status: xhr.status,
          statusText: xhr.statusText,
        });
        return;
      }
      let data: RpcPayload;
      let length: number;
      try {
        const waiting = xhr.responseText.length - processed;
        if (waiting < HEADER_LENGTH) break;
        const header = xhr.responseText.substring(
          processed,
          processed + HEADER_LENGTH
        );
        length = parseInt(header, 10);
        if (isNaN(length)) throw new Error("Not a number: " + header);
        if (waiting < HEADER_LENGTH + length) break;
        const payload = xhr.responseText.substring(
          processed + HEADER_LENGTH,
          processed + HEADER_LENGTH + length
        );
        data = JSON.parse(payload) as RpcPayload;
      } catch (error: unknown) {
        const errorString = String(error);
        fail("Network error: RPC parse error: " + errorString, {
          subtype: "parse",
          error: errorString,
          responseText: xhr.responseText,
        });
        return;
      }
      const current = calls[results];
      const logName = current?.name || calls.map((r) => r.name).join(",");
      if ("announcement_html" in data) {
        console.debug("Received new announcement:", data.announcement_html);
        Votr.settings.announcement_html = data.announcement_html;
      } else if ("log" in data) {
        console.debug("Received " + logName + " log:", data.log, data.message);
        ajaxLogs.push(data);
      } else if ("result" in data) {
        const result = data.result;
        if (!current) {
          fail("Network error: Too many results", { subtype: "many", result });
          return;
        }
        console.debug("Received " + logName + " result:", result);
        try {
          current.callback(result);
        } catch (callbackError) {
          setTimeout(() => {
            throw callbackError;
          }, 0);
        }
        results++;
      } else if ("error" in data) {
        console.log("Received " + logName + " error:", data.error);
        fail(data.error, null);
        return;
      } else {
        fail("Network error: Unknown message type", { subtype: "data", data });
        return;
      }
      processed += HEADER_LENGTH + length;
    }
    if (xhr.readyState == 4) {
      if (processed !== xhr.responseText.length || results !== calls.length) {
        fail("Network error: Incomplete response", {
          subtype: "incomplete",
          processed,
          results,
          length: xhr.responseText.length,
        });
        return;
      }
      finished = true;
    }
    Votr.updateRoot();
  }

  function fail(e: string, reportData: object | null) {
    if (finished) return;
    finished = true;
    console.error("FAILED!", e, reportData);
    if (reportData) {
      const fullData = { responseURL: xhr.responseURL, ...reportData };
      reportClientError("network", fullData);
    }
    if (!Votr.ajaxError) {
      Votr.ajaxError = e;
      Votr.updateRoot();
    }
  }

  const xhr = new XMLHttpRequest();
  xhr.onload = update;
  xhr.onprogress = update;
  xhr.onerror = () => fail("Network error", null);
  xhr.open("POST", "rpc?names=" + calls.map((r) => r.name).join(","), true);
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.setRequestHeader("X-CSRF-Token", Votr.settings.csrf_token!);
  xhr.send("[" + calls.map((r) => r.stringifiedArgs).join(",") + "]");
}

export function sendRpc<N extends keyof Rpcs>(
  name: N,
  args: Parameters<Rpcs[N]>,
  callback: (result: ReturnType<Rpcs[N]>) => void
) {
  sendRawRpcs([
    {
      name,
      stringifiedArgs: JSON.stringify(args),
      callback: (result: unknown) => {
        callback(result as ReturnType<Rpcs[N]>);
      },
    },
  ]);
}

Votr.ajaxError = null;

export const ajaxLogs: RpcLogPayload[] = [];

type CacheEntry<N extends keyof Rpcs> = ReturnType<Rpcs[N]> | undefined;
type CacheMap<N extends keyof Rpcs> = Record<string, CacheEntry<N>>;

const requestCache: { [N in keyof Rpcs]?: CacheMap<N> } = {};

let ajaxCallsBatch: RpcCall[] | null = null;

function sendCachedRequest<N extends keyof Rpcs>(
  name: N,
  stringifiedArgs: string
) {
  const map: CacheMap<N> = (requestCache[name] ||= {});

  // If pending or done, return. E.g. if two components want the same request,
  // first they both render, then both their effects run. Only one of them
  // should send the request. The second effect will see it's already pending.
  if (stringifiedArgs in map) return;

  map[stringifiedArgs] = undefined; // Set it to pending.

  const callback = (result: unknown) => {
    map[stringifiedArgs] = result as ReturnType<Rpcs[N]>; // Set it to done.
  };

  // Start a new batch if needed. All calls in the near future (other calls from
  // this <Loading>, as well as other <Loading>s that were rendered at the same
  // time) will be collected and sent in one HTTP request.
  if (!ajaxCallsBatch) {
    ajaxCallsBatch = [];
    // A microtask would probably work too, but setTimeout is good enough.
    setTimeout(() => {
      const localBatch = ajaxCallsBatch;
      ajaxCallsBatch = null;
      if (localBatch) sendRawRpcs(localBatch);
    }, 0);
  }

  ajaxCallsBatch.push({ name, stringifiedArgs, callback });
}

export function invalidateRequestCache(command: keyof Rpcs) {
  /* eslint-disable-next-line @typescript-eslint/no-dynamic-delete --
   * requestCache is a plain object, not a Map, because TypeScript doesn't
   * support mapped types for Map (all values must have the same type). */
  delete requestCache[command];
}

export class CacheRequester {
  missing: (() => void)[] = [];

  loadedAll = true;

  get<N extends keyof Rpcs>(
    name: N,
    ...args: Parameters<Rpcs[N]>
  ): ReturnType<Rpcs[N]> | undefined {
    const stringifiedArgs = JSON.stringify(args);
    const entry = requestCache[name]?.[stringifiedArgs];
    if (entry !== undefined) {
      return entry;
    } else {
      this.missing.push(() => sendCachedRequest(name, stringifiedArgs));
      this.loadedAll = false;
      return undefined;
    }
  }
}

export function Loading({ requests }: { requests?: (() => void)[] }) {
  // In order to get good RPC batching, if multiple Loading components are
  // mounted at the "same time" (in the same React Commit Phase), we want React
  // to run all their useEffect hooks at the "same time" (preferably in the same
  // microtask, or at least macrotask). As of React 18.2.0, it seems useEffect
  // does work that way. It may or may not run in its own micro/macro(?)task
  // after updating the DOM, but all pending useEffect hooks run together. If it
  // breaks in a future version, let's try switching to useLayoutEffect.
  useEffect(() => {
    if (requests) {
      for (const requestFn of requests) requestFn();
    }
  });

  return <span className="loading">Načítavam...</span>;
}

function goPost(url: string) {
  const form = document.createElement("form");
  form.method = "POST";
  form.action = url;
  document.body.appendChild(form);
  form.submit();
}

export function goLogout() {
  goPost("logout");
}

export function goReset() {
  goPost("reset?destination=" + encodeURIComponent(location.search));
}

export function goResetHome() {
  goPost("reset?destination=");
}

export function reportClientError(type: string, body: object) {
  const xhr = new XMLHttpRequest();
  xhr.open("POST", "report?type=" + type, true);
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.send(JSON.stringify({ location: location.href, ...body }));
}

Votr.dev_ajaxLogs = ajaxLogs;
Votr.dev_sendRpc = sendRpc;
Votr.dev_requestCache = requestCache;
Votr.dev_invalidateRequestCache = invalidateRequestCache;
Votr.dev_goLogout = goLogout;
Votr.dev_goReset = goReset;
Votr.dev_goResetHome = goResetHome;
