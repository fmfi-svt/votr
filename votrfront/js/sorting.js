
import { navigate } from './router';


export var sortAs = {};


sortAs.personName = function (text) {
  var words = text.replace(/,/g, '').split(' ');
  words = _.filter(words, (word) => !word.match(/\.$/));
  words.unshift(words.pop());   // last name goes to the beginning
  return words.join(' ').toLowerCase();
  // TODO: consider using latinise (see fajr).
};


sortAs.number = function (text) {
  return +text.replace(/,/g, '.');
  // TODO: this won't be needed when fladgejt starts returning numbers
};


sortAs.date = function (date) {
  if (date.match(/^\d\d\.\d\d\.\d\d\d\d/)) {
    return date.substring(6, 10) + date.substring(3, 5) + date.substring(0, 2) + date.substring(10);
  }
  return date;
};


sortAs.interval = function (text) {
  var index = text.indexOf('do ');
  if (index == -1) return '';
  return sortAs.date(text.substring(index + 3));
};


export function sortTable(items, columns, query, queryKey) {
  var orderString = query[queryKey] || columns.defaultOrder;
  var order = orderString ? orderString.split(/(?=[ad])/) : [];
  var directions = order.map((o) => o.substring(0, 1) == 'a' ? 'asc' : 'desc');
  var iteratees = order.map((o) => {
    var [label, prop, process, preferDesc] = columns[o.substring(1)];
    return (item) => (process || _.identity)(prop ? item[prop] : item);
  });

  items = _.orderBy(items, iteratees, directions);

  function handleClick(event) {
    var index = event.currentTarget.getAttribute('data-index');
    var [label, prop, process, preferDesc] = columns[index];

    var newOrder = _.without(order, 'a' + index, 'd' + index);
    newOrder.unshift((
      order[0] == 'a' + index ? 'd' :
      order[0] == 'd' + index ? 'a' :
      preferDesc ? 'd' : 'a') + index);

    navigate({ ...query, [queryKey]: newOrder.join('') });
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
