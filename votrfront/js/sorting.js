
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


export function sortTable(items, columns, query, queryKey, fullTable) {
  if (columns[0][0]){
    columns = columns.map(([label, prop, process, preferDesc, hiddenClass]) => ({label, prop, process, preferDesc, hiddenClass}));
  }
  items = items.map((item, index) => ({...item, originalIndex: index}));
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
    {columns.map(({label, shortLabel, prop, process, preferDesc, hiddenClass = []}, index) =>
      <th key={index} data-index={index} onClick={handleClick}
          className={(fullTable ? "" : hiddenClass.join(" ")) + ' sort ' + (order[0] == 'a' + index ? 'asc' :
                                order[0] == 'd' + index ? 'desc' : '')}>
        {shortLabel ? shortLabel : label}
      </th>
    )}
  </tr>;

  return [items, header];
};

export class SortableTable extends React.Component {
  constructor(props) {
    super(props);
    this.state = {};
  }

  toggleInfo(index) {
    this.setState((state) => ({[index]: !state[index]}));
  }

  expandAll() {
    const opened = {};
    for ( let i = 0; i < this.props.items.length; i++ ) {
      opened[i] = true;
    }
    this.setState(opened);
  }

  collapseAll() {
    const opened = {};
    for ( const index in this.state ) {
      opened[index] = false;
    }
    this.setState(opened);
  }

  isOpened(index) {
    return this.state[index];
  }

  allClosed() {
    for (const index in this.state) {
      if (this.state[index]) return false;
    }
    return true;
  }

  render() {
    const {
      items,
      columns,
      queryKey,
      withButtons,
      footer,
      message,
      rowClassName,
      expandedContentOffset = 0
    } = this.props;

    var fullTable = LocalSettings.get('fullTable') == 'true';

    return queryConsumer(query => {
      const [sortedItems, header] = sortTable(
        items,
        columns,
        query,
        queryKey,
        fullTable
      );

      const className =
        "table table-condensed table-bordered table-striped table-hover" +
        (withButtons ? " with-buttons-table" : "");

      const notExpandable = columns.reduce(
        (acc, col) =>
          acc.filter(item => !(col.hiddenClass && col.hiddenClass.includes(item))),
        ["hidden-xs", "hidden-sm", "hidden-md", "hidden-lg"]
      );

      function revertHidden(hiddenClass) {
        const all = ["hidden-xs", "hidden-sm", "hidden-md", "hidden-lg"];
        return all.filter(size => !hiddenClass.includes(size)).join(" ");
      }

      const rows = [];

      sortedItems.forEach((item) => {
        rows.push(
          <tr
            key={item.originalIndex}
            onClick={() => !fullTable && this.toggleInfo(item.originalIndex)}
            className={rowClassName && rowClassName(item)}
          >
            {columns.map(
              ({
                label,
                prop,
                process,
                hiddenClass = [],
                cell,
                colProps,
                expansionMark
              }, index) => (
                <td
                  key={index}
                  className={!fullTable ? hiddenClass.join(" ") : ""}
                  {...(colProps ? colProps(item) : {})}
                >
                  {expansionMark && !fullTable && (
                    <span className={`${notExpandable.join(" ")} expand-arrow ${
                      this.isOpened(item.originalIndex) ? "arrow-expanded" : "arrow-collapsed"}`}/>
                  )}
                  {cell ? cell(item, query) : item[prop]}
                </td>
              )
            )}
          </tr>
        );

        if (!fullTable){
          rows.push(<tr key={`${item.originalIndex}-striped-hack`} className={"hidden"} />);

          rows.push(
            <tr
              key={`${item.originalIndex}-info`}
              className={`${notExpandable.join(" ")} ${
                this.isOpened(item.originalIndex) ? "" : "hidden"
              }`}
            >
              {expandedContentOffset > 0 && <td colSpan={expandedContentOffset} />}
              <td colSpan={columns.length - expandedContentOffset}>
                <table className="table-condensed">
                  <tbody>
                    {columns
                      .filter(col => col.hiddenClass)
                      .map((col, index) => (
                        <tr key={index} className={revertHidden(col.hiddenClass)}>
                          <td>{col.label}:</td>
                          <td>{col.cell ? col.cell(item, query) : item[col.prop]}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </td>
            </tr>
          );
        }
      });

      return (
        <div>
          <div className={`btn-toolbar section ${notExpandable.join(" ")}`}>
            <button
              className={"btn btn-default" + (fullTable ? " active" : "")}
              onClick={() => {
                LocalSettings.set("fullTable", !fullTable);
              }}
            >Zobraziť celú tabuľku</button>
            {!fullTable && <button
              className={"btn btn-default"}
              onClick={() => (this.allClosed() ? this.expandAll() : this.collapseAll())}
            >
              {this.allClosed() ? "Rozbaliť všetky" : "Zabaliť všetky"}
            </button>}
          </div>
          <table className={className}>
            <thead>{header}</thead>
            <tbody>{rows}</tbody>
            {(footer || message) && (
              <tfoot>
                {footer && footer(fullTable)}
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
  }
}
