
console.log('hello!');

function sendRpc(name, args, callback) {
  var HEADER_LENGTH = 10;
  var processed = 0;
  var result = undefined;

  function update(e) {
    while (true) {
      var waiting = xhr.responseText.length - processed;
      if (waiting < HEADER_LENGTH) break;
      var header = xhr.responseText.substr(processed, HEADER_LENGTH);
      var length = parseInt(header, HEADER_LENGTH);
      if (waiting < HEADER_LENGTH + length) break;
      var payload = xhr.responseText.substr(processed + HEADER_LENGTH, length);
      var data = JSON.parse(payload);
      console.log('RECEIVED', data);
      if (data.result) result = data.result;
      processed += HEADER_LENGTH + length;
    }
    if (xhr.readyState == 4) {
      if (processed != xhr.responseText.length) {
        console.log('INCOMPLETE!'); // TODO
      }
      if (callback) {
        callback(result);
      }
    }
  }

  function fail(e) {
    console.log("FAILED!"); // TODO
  }

  var xhr = new XMLHttpRequest();
  xhr.onload = update;
  xhr.onprogress = update;
  xhr.onerror = fail;
  xhr.open("POST", "rpc?name=" + name, true);
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.send(JSON.stringify(args));
}

// $('<form method="POST" action="login?server=0&type=cosigncookie&to="></form>').appendTo('body').submit()
// sendRpc('get_studia', [])
// sendRpc('get_zapisne_listy', ['INF'])
