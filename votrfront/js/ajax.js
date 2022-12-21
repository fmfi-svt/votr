
import React, { useEffect } from 'react';
import _ from 'lodash';

export function sendRpc(name, args, callback) {
  var HEADER_LENGTH = 10;
  var processed = 0;
  var result = undefined;
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
      var data = JSON.parse(payload);
      console.log('RECEIVED', data);
      if (data.log !== undefined) logs.push(data);
      if (data.result !== undefined) result = data.result;
      if (data.error !== undefined) return fail(data.error);
      processed += HEADER_LENGTH + length;
    }
    if (xhr.readyState == 4) {
      if (processed != xhr.responseText.length || result === undefined) {
        console.log('INCOMPLETE!');
        return fail("Network error: Incomplete response");
      }
      finished = true;
      if (callback) {
        callback(result);
      }
    }
    Votr.appRoot.forceUpdate();
  }

  function fail(e) {
    if (finished) return;
    finished = true;
    console.log("FAILED!", e);
    if (!Votr.ajaxError) {
      Votr.ajaxError = _.isString(e) ? e : "Network error";
      Votr.appRoot.forceUpdate();
    }
  }

  var xhr = new XMLHttpRequest();
  xhr.onload = update;
  xhr.onprogress = update;
  xhr.onerror = fail;
  xhr.open("POST", "rpc?name=" + name, true);
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.setRequestHeader("X-CSRF-Token", Votr.settings.csrf_token);
  xhr.send(JSON.stringify(args));
}


Votr.ajaxError = null;


export var logs = [];


export var RequestCache = {};

RequestCache.pending = {};

RequestCache.sendRequest = function (request) {
  var cacheKey = request.join('\0');
  if (RequestCache[cacheKey]) return;
  if (RequestCache.pending[cacheKey]) return;
  RequestCache.pending[cacheKey] = true;
  sendRpc(request[0], request.slice(1), function (result) {
    RequestCache[cacheKey] = result;
  });
};

RequestCache.invalidate = function (command) {
  for (var key in RequestCache) {
    if (key.split('\0')[0] === command) {
      delete RequestCache[key];
    }
  }

  for (var key in RequestCache.pending) {
    if (key.split('\0')[0] === command) {
      delete RequestCache.pending[key];
    }
  }
}


export function CacheRequester() {
  this.missing = [];
  this.loadedAll = true;
};

CacheRequester.prototype.get = function (...request) {
  var cacheKey = request.join('\0');
  if (RequestCache[cacheKey] !== undefined) {
    return RequestCache[cacheKey];
  } else {
    this.missing.push(request);
    this.loadedAll = false;
    return null;
  }
};


export function Loading({ requests }) {
  useEffect(() => {
    if (requests) requests.forEach((request) => {
      RequestCache.sendRequest(request);
    });
  });

    return <span className="loading">Načítavam...</span>;
}


export function goPost(url) {
  var form = document.createElement('form');
  form.method = 'POST';
  form.action = url;
  document.body.appendChild(form);
  form.submit();
};

export function goLogout() {
  goPost('logout');
};

export function goReset() {
  goPost('reset?destination=' + encodeURIComponent(location.search));
};

export function goResetHome() {
  goPost('reset?destination=');
};
