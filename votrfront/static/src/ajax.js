/**
 * @jsx React.DOM
 * @require react.min.js
 */

(function () {


Votr.sendRpc = function (name, args, callback) {
  var HEADER_LENGTH = 10;
  var processed = 0;
  var result = undefined;
  var failed = false;

  function update(e) {
    if (failed) return;
    while (true) {
      var waiting = xhr.responseText.length - processed;
      if (waiting < HEADER_LENGTH) break;
      var header = xhr.responseText.substr(processed, HEADER_LENGTH);
      var length = parseInt(header, HEADER_LENGTH);
      if (waiting < HEADER_LENGTH + length) break;
      var payload = xhr.responseText.substr(processed + HEADER_LENGTH, length);
      var data = JSON.parse(payload);
      console.log('RECEIVED', data);
      if (data.result !== undefined) result = data.result;
      if (data.error !== undefined) return fail(data.error);
      processed += HEADER_LENGTH + length;
    }
    if (xhr.readyState == 4) {
      if (processed != xhr.responseText.length) {
        console.log('INCOMPLETE!'); // TODO
        alert('INCOMPLETE!')
      }
      if (callback && result !== undefined) {
        callback(result);
      }
    }
  }

  function fail(e) {
    if (failed) return;
    failed = true;
    console.log("FAILED!", e); // TODO
    alert("FAILED!\n" + e);
  }

  var xhr = new XMLHttpRequest();
  xhr.onload = update;
  xhr.onprogress = update;
  xhr.onerror = fail;
  xhr.open("POST", "rpc?name=" + name, true);
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.send(JSON.stringify(args));
}


Votr.RequestCache = {};

Votr.RequestCache.pending = {};

Votr.RequestCache.sendRequest = function (request) {
  var cacheKey = request.join('\0');
  if (Votr.RequestCache[cacheKey]) return;
  if (Votr.RequestCache.pending[cacheKey]) return;
  Votr.RequestCache.pending[cacheKey] = true;
  Votr.sendRpc(request[0], request.slice(1), function (result) {
    Votr.RequestCache[cacheKey] = result;
    Votr.appRoot.forceUpdate();
  });
};


Votr.CacheRequester = function () {
  this.missing = [];
  this.loadedAll = true;
};

Votr.CacheRequester.prototype.get = function () {
  var request = Array.prototype.slice.call(arguments);
  var cacheKey = request.join('\0');
  if (Votr.RequestCache[cacheKey]) {
    return Votr.RequestCache[cacheKey];
  } else {
    this.missing.push(request);
    this.loadedAll = false;
    return null;
  }
};


Votr.Loading = React.createClass({
  componentDidMount: function () {
    if (this.props.requests) this.props.requests.forEach((request) => {
      Votr.RequestCache.sendRequest(request);
    });
  },

  componentDidUpdate: function () {
    if (this.props.requests) this.props.requests.forEach((request) => {
      Votr.RequestCache.sendRequest(request);
    });
  },

  render: function () {
    return <span>Loading...</span>;
  }
});


})();
