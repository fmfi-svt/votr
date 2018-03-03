import React, { Component } from 'react';
import $ from 'jquery';

const debug = function(...args) {
  if (process.env.NODE_ENV !== 'production') {
    // eslint-disable-next-line
    console.log(...args);
  }
};

export function sendRpc(name, args, callback) {
  const HEADER_LENGTH = 10;
  let processed = 0;
  let result;
  let finished = false;
  const xhr = new XMLHttpRequest();

  function update() {
    if (finished) return;
    while (true) {
      const waiting = xhr.responseText.length - processed;
      if (waiting < HEADER_LENGTH) {
        break;
      }
      const header = xhr.responseText.substr(processed, HEADER_LENGTH);
      const length = parseInt(header, HEADER_LENGTH);
      if (waiting < HEADER_LENGTH + length) {
        break;
      }
      const payload = xhr.responseText.substr(processed + HEADER_LENGTH, length);
      const data = JSON.parse(payload);
      debug('RECEIVED', data);
      if (data.log !== undefined) {
        logs.push(data);
      }
      if (data.result !== undefined) {
        result = data.result;
      }
      if (data.error !== undefined) {
        return fail(data.error);
      }
      processed += HEADER_LENGTH + length;
    }
    if (xhr.readyState === 4) {
      if (processed !== xhr.responseText.length || result === undefined) {
        debug('INCOMPLETE!');
        return fail('Network error: Incomplete response');
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
    debug('FAILED!', e);
    if (!Votr.ajaxError) {
      Votr.ajaxError = (typeof e === 'string' || e instanceof String) ? e : 'Network error';
      Votr.appRoot.forceUpdate();
    }
  }

  xhr.onload = update;
  xhr.onprogress = update;
  xhr.onerror = fail;
  xhr.open('POST', 'rpc?name=' + name, true);
  xhr.setRequestHeader('Content-Type', 'application/json');
  xhr.setRequestHeader('X-CSRF-Token', Votr.settings.csrf_token);
  xhr.send(JSON.stringify(args));
}

Votr.ajaxError = null;

export const logs = [];

export const RequestCache = {};

RequestCache.pending = {};

RequestCache.sendRequest = function (request) {
  const cacheKey = request.join('\0');
  if (RequestCache[cacheKey]) {
    return;
  }
  if (RequestCache.pending[cacheKey]) {
    return;
  }
  RequestCache.pending[cacheKey] = true;
  sendRpc(request[0], request.slice(1), (result) => {
    RequestCache[cacheKey] = result;
  });
};

RequestCache.invalidate = function(command) {
  for (let key in RequestCache) {
    if (key.split('\0')[0] === command) {
      delete RequestCache[key];
    }
  }

  for (let key in RequestCache.pending) {
    if (key.split('\0')[0] === command) {
      delete RequestCache.pending[key];
    }
  }
};

export function CacheRequester() {
  this.missing = [];
  this.loadedAll = true;
};

CacheRequester.prototype.get = function(...request) {
  const cacheKey = request.join('\0');
  if (RequestCache[cacheKey] !== undefined) {
    return RequestCache[cacheKey];
  } else {
    this.missing.push(request);
    this.loadedAll = false;
    return null;
  }
};

export class Loading extends Component {
  componentDidMount() {
    if (this.props.requests) {
      this.props.requests.forEach(
        (request) => {RequestCache.sendRequest(request);}
      );
    }
  }

  componentDidUpdate() {
    if (this.props.requests) {
      this.props.requests.forEach(
        (request) => {RequestCache.sendRequest(request);}
      );
    }
  }

  render() {
    return <span className="loading">Načítavam...</span>;
  }
}


export const goPost = (url) => {
  $('<form/>', { method: 'POST', action: url, appendTo: 'body' }).submit();
};

export const goLogout = () => {
  goPost('logout');
};

export const goReset = () => {
  goPost('reset?destination=' + encodeURIComponent(location.search));
};

export const goResetHome = () => {
  goPost('reset?destination=');
};
