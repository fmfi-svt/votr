
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
  if (columns[0][0]){
    columns = columns.map(([label, prop, process, preferDesc, hiddenClass]) => ({label, prop, process, preferDesc, hiddenClass}));
  }
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

export class SortableTable extends React.Component {
  constructor(props) {
    super(props);
    this.state = {};
  }

  toggleInfo(index) {
    this.setState((state) => ({[index]: !state[index]}));
  }

  expandAll(items) {
    const opened = {};
    for ( const i = 0; i < items.length; i++ ) {
      opened[i] = true;
    }
    this.setState(opened);
  }

  // TODO: better names
  collapseAll() {
    const opened = {};
    for ( const i = 0; i < items.length; i++ ) {
      opened[i] = false;
    }
    this.setState(opened);
  }

  isOpened(index) {
    return this.state[index];
  }

  render() {
    const {items, columns, queryKey, withButtons, footer, message} = this.props;

    return queryConsumer(query => {
      const [sortedItems, header] = sortTable(
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

      function revertHidden(hiddenClass) {
        const all = ["hidden-xs", "hidden-sm", "hidden-md", "hidden-lg"];
        return all.filter(size => !hiddenClass.includes(size)).join(" ");
      }

      const rows = [];

      sortedItems.forEach((item, index) => {
        rows.push(
          <tr key={index} onClick={() => this.toggleInfo(index)}>
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
                  {...(colProps ? colProps(item) : {})}
                >
                  {expansionMark && (
                    <span
                      className={notExpandable.join(" ")}
                      style={{ fontWeight: "bold", float: "right" }}
                    >
                      {this.isOpened(index) ? "-" : "+"}
                    </span>
                  )}
                  {cell ? cell(item, query) : item[prop]}
                </td>
              )
            )}
          </tr>
        );

        rows.push(<tr key={`${index}-striped-hack`} className={"hidden"} />);

        rows.push(
          <tr
            key={`${index}-info`}
            className={`${notExpandable.join(" ")} ${
              this.isOpened(index) ? "" : "hidden"
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
                          {col.cell ? col.cell(item, query) : item[col.prop]}
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
            <button className="btn btn-default hidden-md hidden-lg" onClick={() => this.expandAll(sortedItems)}>Expand all</button>
            <button className="btn btn-default hidden-md hidden-lg" onClick={this.collapseAll}>Collapse all</button>
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
  }
}
