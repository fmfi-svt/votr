import React, { useEffect } from "react";
import _ from "lodash";
import { Rpcs } from "./types";

interface RpcLogPayload {
  log: string;
  message: string;
  time: number;
}
interface RpcErrorPayload {
  error: string;
}
interface RpcResultPayload {
  result: {};
}
type RpcPayload = RpcLogPayload | RpcErrorPayload | RpcResultPayload;

export function sendRpc<N extends keyof Rpcs>(
  name: N,
  args: Parameters<Rpcs[N]>,
  callback: (result: ReturnType<Rpcs[N]>) => void
) {
  var HEADER_LENGTH = 10;
  var processed = 0;
  var result: {} | undefined = undefined;
  var finished = false;

  function update() {
    if (finished) return;
    while (true) {
      var waiting = xhr.responseText.length - processed;
      if (waiting < HEADER_LENGTH) break;
      var header = xhr.responseText.substr(processed, HEADER_LENGTH);
      var length = parseInt(header, HEADER_LENGTH);
      if (waiting < HEADER_LENGTH + length) break;
      var payload = xhr.responseText.substr(processed + HEADER_LENGTH, length);
      var data = JSON.parse(payload) as RpcPayload;
      console.log("RECEIVED", data);
      if ("log" in data) ajaxLogs.push(data);
      if ("result" in data) result = data.result;
      if ("error" in data) return fail(data.error);
      processed += HEADER_LENGTH + length;
    }
    if (xhr.readyState == 4) {
      if (processed != xhr.responseText.length || result === undefined) {
        console.log("INCOMPLETE!");
        return fail("Network error: Incomplete response");
      }
      finished = true;
      if (callback) {
        callback(result as ReturnType<Rpcs[N]>);
      }
    }
    Votr.updateRoot();
  }

  function fail(e: unknown) {
    if (finished) return;
    finished = true;
    console.log("FAILED!", e);
    if (!Votr.ajaxError) {
      Votr.ajaxError = _.isString(e) ? e : "Network error";
      Votr.updateRoot();
    }
  }

  var xhr = new XMLHttpRequest();
  xhr.onload = update;
  xhr.onprogress = update;
  xhr.onerror = fail;
  xhr.open("POST", "rpc?name=" + name, true);
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.setRequestHeader("X-CSRF-Token", Votr.settings.csrf_token!);
  xhr.send(JSON.stringify(args));
}

Votr.ajaxError = null;

export var ajaxLogs: RpcLogPayload[] = [];

export var RequestCache: {
  done: Record<string, unknown>;
  pending: Record<string, true>;
  pocet_prihlasenych_je_stary: Record<string, true>;
} = { done: {}, pending: {}, pocet_prihlasenych_je_stary: {} };

function sendCachedRequest<N extends keyof Rpcs>(
  request: [N, ...Parameters<Rpcs[N]>]
) {
  var cacheKey = request.join("\0");
  if (RequestCache.done[cacheKey]) return;
  if (RequestCache.pending[cacheKey]) return;
  RequestCache.pending[cacheKey] = true;
  var [name, ...args] = request;
  sendRpc(name, args, function (result) {
    RequestCache.done[cacheKey] = result;
  });
}

export function invalidateRequestCache(command: string) {
  for (var key in RequestCache.done) {
    if (key.split("\0")[0] === command) {
      delete RequestCache.done[key];
    }
  }

  for (var key in RequestCache.pending) {
    if (key.split("\0")[0] === command) {
      delete RequestCache.pending[key];
    }
  }
}

export class CacheRequester {
  missing: Array<() => void> = [];
  loadedAll = true;
  get<N extends keyof Rpcs>(
    ...request: [N, ...Parameters<Rpcs[N]>]
  ): ReturnType<Rpcs[N]> | null {
    var cacheKey = request.join("\0");
    if (RequestCache.done[cacheKey] !== undefined) {
      return RequestCache.done[cacheKey] as ReturnType<Rpcs[N]>;
    } else {
      this.missing.push(() => sendCachedRequest(request));
      this.loadedAll = false;
      return null;
    }
  }
}

export function Loading({ requests }: { requests?: Array<() => void> }) {
  useEffect(() => {
    if (requests) {
      for (const requestFn of requests) requestFn();
    }
  });

  return <span className="loading">Načítavam...</span>;
}

function goPost(url: string) {
  var form = document.createElement("form");
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

Votr.dev_sendRpc = sendRpc;
Votr.dev_RequestCache = RequestCache;
Votr.dev_invalidateRequestCache = invalidateRequestCache;
Votr.dev_goLogout = goLogout;
Votr.dev_goReset = goReset;
Votr.dev_goResetHome = goResetHome;
