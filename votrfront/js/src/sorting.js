import React from 'react';

import { navigate } from './router';

export const sortAs = {};

sortAs.personName = (text) => {
  let words = text.replace(/,/g, '').split(' ');
  words = words.filter((word) => !word.match(/\.$/));
  // last name goes to the beginning
  words.unshift(words.pop());
  return words.join(' ').toLowerCase();
  // TODO: consider using latinise (see fajr).
};


sortAs.number = (text) => {
  return +text.replace(/,/g, '.');
  // TODO: this won't be needed when fladgejt starts returning numbers
};


sortAs.date = (date) => {
  if (date.match(/^\d\d\.\d\d\.\d\d\d\d/)) {
    return date.substring(6, 10) + date.substring(3, 5) + date.substring(0, 2) + date.substring(10);
  }
  return date;
};


sortAs.interval = (text) => {
  const index = text.indexOf('do ');
  if (index === -1) {
    return '';
  }
  return sortAs.date(text.substring(index + 3));
};

export const sortTable = (items, columns, query, queryKey) => {
  const orderString = query[queryKey] || columns.defaultOrder;
  const order = orderString ? orderString.split(/(?=[ad])/) : [];
  const orderLength = order.length;
  const orderAsc = order.map((orderItem) => orderItem.substring(0, 1) === 'a');
  const orderColumns = order.map((orderItem) => columns[orderItem.substring(1)]);

  items = items.map((item, index) => {
    const criteria = [];
    for (let i = 0; i < orderLength; i++) {
      const [label, prop, process, preferDesc] = orderColumns[i];
      let value = prop ? item[prop] : item;
      if (process) {
        value = process(value);
      }
      if (!prop && !process) {
        value = undefined;
      }
      criteria.push(value);
    }
    return { item, index, criteria };
  });

  items.sort((a, b) => {
    for (let i = 0; i < orderLength; i++) {
      const ac = a.criteria[i], bc = b.criteria[i];
      if (ac === bc) {
        continue;
      }
      if (ac < bc) {
        return orderAsc[i] ? -1 : 1;
      }
      if (ac > bc) {
        return orderAsc[i] ? 1 : -1;
      }
    }
    return a.index - b.index;
  });

  items = items.map((a) => a.item);

  const handleClick = (event) => {
    const index = event.currentTarget.getAttribute('data-index');
    const [label, prop, process, preferDesc] = columns[index];

    const newOrder = order.filter(
      (ord) => ord !== 'a' + index && ord !== 'd' + index
    );
    newOrder.unshift((
      order[0] === 'a' + index ? 'd' :
        order[0] === 'd' + index ? 'a' :
          preferDesc ? 'd' : 'a'
    ) + index);

    navigate({ ...query, [queryKey]: newOrder.join('') });
  };

  const header = (
    <tr>
      {columns.map(([label, prop, process, preferDesc], index) => (
        <th
          key={index}
          data-index={index}
          onClick={handleClick}
          className={
            'sort ' + (order[0] === 'a' + index ? 'asc' :
              order[0] === 'd' + index ? 'desc' : '')
          }
        >
          {label}
        </th>
      ))}
    </tr>
  );

  return [items, header];
};
