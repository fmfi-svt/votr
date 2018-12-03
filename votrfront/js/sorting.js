
import React from 'react';
import _ from 'lodash';
import { navigate, queryConsumer } from './router';
import { LocalSettings } from './LocalSettings';


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
    {columns.map(([label, prop, process, preferDesc, hiddenClass], index) =>
      <th key={index} data-index={index} onClick={handleClick}
          className={`${hiddenClass} ` + 'sort ' + (order[0] == 'a' + index ? 'asc' :
                                order[0] == 'd' + index ? 'desc' : '')}>
        {label}
      </th>
    )}
  </tr>;

  return [items, header];
};

export function sortTableCopyForObjectCol(items, columns, query, queryKey) {
  var orderString = query[queryKey] || columns.defaultOrder;
  var order = orderString ? orderString.split(/(?=[ad])/) : [];
  var directions = order.map((o) => o.substring(0, 1) == 'a' ? 'asc' : 'desc');
  var iteratees = order.map((o) => {
    var {label, prop, process, preferDesc} = columns[o.substring(1)];
    return (item) => (process || _.identity)(prop ? item[prop] : item);
  });

  items = _.orderBy(items, iteratees, directions);

  function handleClick(event) {
    var index = event.currentTarget.getAttribute('data-index');
    var {label, prop, process, preferDesc} = columns[index];

    var newOrder = _.without(order, 'a' + index, 'd' + index);
    newOrder.unshift((
      order[0] == 'a' + index ? 'd' :
      order[0] == 'd' + index ? 'a' :
      preferDesc ? 'd' : 'a') + index);

    navigate({ ...query, [queryKey]: newOrder.join('') });
  }

  var header = <tr>
    {columns.map(({label, prop, process, preferDesc, hiddenClass = []}, index) =>
      <th key={index} data-index={index} onClick={handleClick}
          className={`${hiddenClass.join(" ")} ` + 'sort ' + (order[0] == 'a' + index ? 'asc' :
                                order[0] == 'd' + index ? 'desc' : '')}>
        {label}
      </th>
    )}
  </tr>;

  return [items, header];
};

function toggleInfo(index) {
  const opened = JSON.parse(LocalSettings.get("openedRows")) || {};
  opened[index] = !opened[index];
  LocalSettings.set("openedRows", JSON.stringify(opened));
}

function expandAll(items) {
  const opened = items.reduce((acc, curr, idx) => ({...acc, [idx]: true}), {});
  LocalSettings.set("openedRows", JSON.stringify(opened));
}

// TODO: better names
function collapseAll() {
  LocalSettings.set("openedRows", JSON.stringify({}));
}

function isOpened(index) {
  return (JSON.parse(LocalSettings.get("openedRows")) || {})[index];
}

export const SortableTable = ({
  items,
  columns,
  queryKey,
  withButtons,
  footer,
  message
}) =>
  queryConsumer(query => {
    // TODO change to sortTable
    const [sortedItems, header] = sortTableCopyForObjectCol(
      items,
      columns,
      query,
      queryKey
    );

    const className =
      "table table-condensed table-bordered table-striped table-hover" +
      (withButtons ? " with-buttons-table" : "");

    const notExpandable = columns.reduce(
      (acc, col) =>
        acc.filter(item => !(col.hiddenClass && col.hiddenClass.includes(item))),
      ["hidden-xs", "hidden-sm", "hidden-md", "hidden-lg"]
    );

    const rows = [];

    sortedItems.forEach((item, index) => {
      rows.push(
        <tr key={index} onClick={() => toggleInfo(index)}>
          {columns.map(
            ({
              label,
              prop,
              process,
              hiddenClass = [],
              cell,
              colProps,
              expansionMark
            }) => (
              <td
                key={label}
                className={hiddenClass.join(" ")}
                {...(colProps instanceof Function ? colProps(item) : {})}
              >
                {expansionMark && (
                  <span
                    className={notExpandable.join(" ")}
                    style={{ fontWeight: "bold", float: "right" }}
                  >
                    {isOpened(index) ? "-" : "+"}
                  </span>
                )}
                {cell instanceof Function ? cell(item, query) : item[prop]}
              </td>
            )
          )}
        </tr>
      );

      rows.push(<tr key={`${index}-striped-hack`} className={"hidden"} />);

      function revertHidden(hiddenClass) {
        const all = ["hidden-xs", "hidden-sm", "hidden-md", "hidden-lg"];
        return all.filter(size => !hiddenClass.includes(size)).join(" ");
      }

      rows.push(
        <tr
          key={`${index}-info`}
          className={`${notExpandable.join(" ")} ${
            isOpened(index) ? "" : "hidden"
          }`}
        >
          {withButtons && <td />}
          <td colSpan={withButtons ? columns.length - 1 : columns.length}>
            <table className="table-condensed">
              <tbody>
                {columns
                  .filter(col => col.hiddenClass)
                  .map(col => (
                    <tr
                      key={col.label}
                      className={revertHidden(col.hiddenClass)}
                    >
                      <td>{col.label}:</td>
                      <td>
                        {col.cell instanceof Function ? col.cell(item, query) : item[col.prop]}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </td>
        </tr>
      );
    });

    return (
      <div>
        <div style={{marginBottom: "5px"}}>
          <button className="btn btn-default hidden-md hidden-lg" onClick={() => expandAll(sortedItems)}>Expand all</button>
          <button className="btn btn-default hidden-md hidden-lg" onClick={collapseAll}>Collapse all</button>
        </div>
        <table className={className}>
          <thead>{header}</thead>
          <tbody>{rows}</tbody>
          {(footer || message) && (
            <tfoot>
              {footer}
              {message && (
                <tr>
                  <td colSpan={columns.length}>{message}</td>
                </tr>
              )}
            </tfoot>
          )}
        </table>
      </div>
    );
  });
