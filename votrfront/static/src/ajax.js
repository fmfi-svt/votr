/**
 * @jsx React.DOM
 * @dontdepend Votr.ajaxError
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
      if (data.log !== undefined) Votr.logs.push(data);
      if (data.result !== undefined) result = data.result;
      if (data.error !== undefined) return fail(data.error);
      processed += HEADER_LENGTH + length;
    }
    if (xhr.readyState == 4) {
      if (processed != xhr.responseText.length || result === undefined) {
        console.log('INCOMPLETE!');
        fail("Network error: Incomplete response");
      }
      if (callback) {
        callback(result);
      }
    }
    Votr.appRoot.forceUpdate();
  }

  function fail(e) {
    if (failed) return;
    failed = true;
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


Votr.logs = [];


Votr.RequestCache = {};

Votr.RequestCache.pending = {};

Votr.RequestCache.sendRequest = function (request) {
  var cacheKey = request.join('\0');
  if (Votr.RequestCache[cacheKey]) return;
  if (Votr.RequestCache.pending[cacheKey]) return;
  Votr.RequestCache.pending[cacheKey] = true;
  Votr.sendRpc(request[0], request.slice(1), function (result) {
    Votr.RequestCache[cacheKey] = result;
  });
};


Votr.CacheRequester = function () {
  this.missing = [];
  this.loadedAll = true;
};

Votr.CacheRequester.prototype.get = function () {
  var request = Array.prototype.slice.call(arguments);
  var cacheKey = request.join('\0');
  if (Votr.RequestCache[cacheKey] !== undefined) {
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
    return <span className="loading">Načítavam...</span>;
  }
});


Votr.goPost = function (url) {
  $('<form/>', { method: 'POST', action: url, appendTo: 'body' }).submit();
};

Votr.goLogout = function () {
  Votr.goPost('logout');
};

Votr.goReset = function () {
  // TODO: Since the query string itself might have errors (nonexistent keys
  // and the like), consider always returning to the front page.
  Votr.goPost('reset?destination=' + encodeURIComponent(location.search));
};


})();
