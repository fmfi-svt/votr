/** @jsx React.DOM */

(function () {


Votr.sortAs = {};


Votr.sortAs.personName = function (text) {
  var words = text.replace(/,/g, '').split(' ');
  words = _.filter(words, (word) => !word.match(/\.$/));
  words.push(words.shift());   // first name goes to the end
  return words.join(' ').toLowerCase();
  // TODO: consider using latinise (see fajr).
};


Votr.sortAs.number = function (text) {
  return +text.replace(/,/g, '.');
  // TODO: this won't be needed when fladgejt starts returning numbers
};


Votr.sortAs.date = function (date) {
  if (date.match(/^\d\d\.\d\d\.\d\d\d\d/)) {
    return date.substring(6, 10) + date.substring(3, 5) + date.substring(0, 2) + date.substring(10);
  }
  return date;
};


Votr.sortAs.interval = function (text) {
  var index = text.indexOf('do ');
  if (index == -1) return '';
  return Votr.sortAs.date(text.substring(index + 3));
};


Votr.sortTable = function (items, columns, query, queryKey) {
  var orderString = query[queryKey] || columns.defaultOrder;
  var order = orderString ? orderString.split(/(?=[ad])/) : [];
  var orderLength = order.length;
  var orderAsc = order.map((orderItem) => orderItem.substring(0, 1) == 'a');
  var orderColumns = order.map((orderItem) => columns[orderItem.substring(1)]);

  items = items.map((item, index) => {
    var criteria = [];
    for (var i = 0; i < orderLength; i++) {
      var [label, prop, process, preferDesc] = orderColumns[i];
      var value = prop ? item[prop] : item;
      if (process) value = process(value);
      if (!prop && !process) value = undefined;
      criteria.push(value);
    }
    return { item, index, criteria };
  });

  items.sort((a, b) => {
    for (var i = 0; i < orderLength; i++) {
      var ac = a.criteria[i], bc = b.criteria[i];
      if (ac === bc) continue;
      if (ac < bc) return orderAsc[i] ? -1 : 1;
      if (ac > bc) return orderAsc[i] ? 1 : -1;
    }
    return a.index - b.index;
  });

  items = items.map((a) => a.item);

  function handleClick(event) {
    var index = event.target.getAttribute('data-index');
    var [label, prop, process, preferDesc] = columns[index];

    var newOrder = _.without(order, 'a' + index, 'd' + index);
    newOrder.unshift((
      order[0] == 'a' + index ? 'd' :
      order[0] == 'd' + index ? 'a' :
      preferDesc ? 'd' : 'a') + index);

    var newQuery = _.assign({}, query);
    newQuery[queryKey] = newOrder.join('');
    Votr.navigate(newQuery);
  }

  var header = <tr>
    {columns.map(([label, prop, process, preferDesc], index) =>
      <th key={index} data-index={index} onClick={handleClick}
          className={'sort ' + (order[0] == 'a' + index ? 'asc' :
                                order[0] == 'd' + index ? 'desc' : '')}>
        {label}
      </th>
    )}
  </tr>;

  return [items, header];
};


})();
