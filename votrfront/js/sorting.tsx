import classNames from "classnames";
import _ from "lodash";
import React, { useContext, useState } from "react";
import { LocalSettings } from "./LocalSettings";
import { ScreenSize, useScreenSize } from "./mediaQueries";
import { navigate, QueryContext } from "./router";
import { Columns, Query } from "./types";

export var sortAs = {
  personName(text: string) {
    var words = text.replace(/,/g, "").split(" ");
    words = _.filter(words, (word) => !word.match(/\.$/));
    var last = words.pop();
    if (last) words.unshift(last); // move last name to the beginning
    return words.join(" ").toLowerCase();
    // TODO: consider using latinise (see fajr).
  },

  number(text: string) {
    return +text.replace(/,/g, ".");
    // TODO: this won't be needed when fladgejt starts returning numbers
  },

  date(date: string) {
    if (date.match(/^\d\d\.\d\d\.\d\d\d\d/)) {
      return (
        date.substring(6, 10) +
        date.substring(3, 5) +
        date.substring(0, 2) +
        date.substring(10)
      );
    }
    return date;
  },

  interval(text: string) {
    var index = text.indexOf("do ");
    if (index == -1) return "";
    return sortAs.date(text.substring(index + 3));
  },
};

function getOrder(
  defaultOrder: string | null | undefined,
  query: Query,
  queryKey: string
): string[] {
  var orderString = query[queryKey] || defaultOrder;
  return orderString ? orderString.split(/(?=[ad])/) : [];
}

function convertOldStyleColumns(columns: Columns): Columns {
  if (columns[0][0]) {
    columns = columns.map(
      ([label, prop, sortKey, preferDesc, hiddenClass]) => ({
        label,
        prop,
        sortKey,
        preferDesc,
        hiddenClass,
      })
    );
  }
  return columns;
}

function sortItems<T>(items: T[], columns: Columns, order: string[]): number[] {
  var directions = order.map((o) => (o.charAt(0) == "a" ? "asc" : "desc"));
  var iteratees = order.map((o) => {
    var { label, prop, sortKey, preferDesc } = columns[Number(o.substring(1))];
    return (originalIndex: number) => {
      var item = items[originalIndex];
      return (sortKey || _.identity)(prop ? (item as any)[prop] : item);
    };
  });
  return _.orderBy(_.range(items.length), iteratees, directions);
}

function renderHeader(
  columns: Columns,
  query: Query,
  queryKey: string,
  order: string[],
  reallyHide: boolean[]
): React.ReactNode {
  function handleClick(event: React.MouseEvent<HTMLElement>) {
    var index = event.currentTarget.getAttribute("data-index");
    var { label, prop, sortKey, preferDesc } = columns[Number(index)];

    var newOrder = _.without(order, "a" + index, "d" + index);
    // prettier-ignore
    newOrder.unshift((
      order[0] == "a" + index ? "d" :
      order[0] == "d" + index ? "a" :
      preferDesc ? "d" : "a") + index);

    navigate({ ...query, [queryKey]: newOrder.join("") });
  }

  return (
    <tr>
      {columns.map(
        ({ label, shortLabel }, index) =>
          !reallyHide[index] && (
            <th
              key={index}
              data-index={index}
              onClick={handleClick}
              className={classNames(
                "sort",
                order[0] == "a" + index && "asc",
                order[0] == "d" + index && "desc"
              )}
            >
              {shortLabel ? shortLabel : label}
            </th>
          )
      )}
    </tr>
  );
}

export function sortTable<T>(
  items: T[],
  columns: Columns,
  query: Query,
  queryKey: string
): [T[], React.ReactNode] {
  var order = getOrder(columns.defaultOrder, query, queryKey);
  columns = convertOldStyleColumns(columns);

  var sortedIndexes = sortItems(items, columns, order);
  var sortedItems = sortedIndexes.map((originalIndex) => items[originalIndex]!);

  var header = renderHeader(columns, query, queryKey, order, []);

  return [sortedItems, header];
}

export function SortableTable<T>({
  items,
  columns,
  queryKey,
  withButtons,
  footer,
  message,
  rowClassName,
  expandedContentOffset = 0,
}: {
  items: T[];
  columns: Columns & { label: React.ReactNode }[];
  queryKey: string;
  withButtons?: boolean;
  footer?: (chosenSize: ScreenSize) => React.ReactNode;
  message?: string | null | undefined;
  rowClassName?: (item: T) => string | undefined;
  expandedContentOffset?: number;
}) {
  var query = useContext(QueryContext);

  var [open, setOpen] = useState<boolean[]>([]);

  var anyOpen = open.includes(true);

  function toggleInfo(index: number) {
    setOpen((open) => {
      open = open.slice();
      open[index] = !open[index];
      return open;
    });
  }

  var fullTable = LocalSettings.get("fullTable") == "true";

  var order = getOrder(columns.defaultOrder, query, queryKey);

  var sortedIndexes = sortItems(items, columns, order);

  var deviceSize = useScreenSize();

  var chosenSize = fullTable ? ScreenSize.LG : deviceSize;

  var canHide = columns.map(
    (column: { hiddenClass?: string[] }) =>
      (deviceSize == ScreenSize.XS &&
        (column.hiddenClass || []).includes("hidden-xs")) ||
      (deviceSize == ScreenSize.SM &&
        (column.hiddenClass || []).includes("hidden-sm"))
  );
  var reallyHide = canHide.map((canHideColumn) => canHideColumn && !fullTable);
  var reallyHiddenCount = _.sum(reallyHide);

  var header = renderHeader(columns, query, queryKey, order, reallyHide);

  const className = classNames(
    "table table-condensed table-bordered table-striped table-hover",
    withButtons && "with-buttons-table"
  );

  const rows = [];

  for (const originalIndex of sortedIndexes) {
    const item = items[originalIndex]!;

    rows.push(
      <tr
        key={originalIndex}
        onClick={(event) => {
          // Don't toggle the row if we just clicked some link or input in the row.
          var target = event.target as Element;
          if (!target.closest("a, input, button") && reallyHiddenCount) {
            toggleInfo(originalIndex);
          }
        }}
        className={rowClassName && rowClassName(item)}
      >
        {columns.map(
          ({ prop, display, cellProps, expansionMark }, index) =>
            !reallyHide[index] && (
              <td key={index} {...(cellProps ? cellProps(item) : {})}>
                {expansionMark && !!reallyHiddenCount && (
                  <span
                    className={classNames(
                      "expand-arrow",
                      open[originalIndex] ? "arrow-expanded" : "arrow-collapsed"
                    )}
                  />
                )}
                {display ? display(item, query) : (item as any)[prop]}
              </td>
            )
        )}
      </tr>
    );

    if (reallyHiddenCount && open[originalIndex]) {
      rows.push(
        <tr key={`${originalIndex}-striped-hack`} className="hidden" />,
        <tr key={`${originalIndex}-info`}>
          {expandedContentOffset > 0 && <td colSpan={expandedContentOffset} />}
          <td
            colSpan={columns.length - reallyHiddenCount - expandedContentOffset}
          >
            <table className="table-condensed">
              <tbody>
                {columns.map(
                  (col, index) =>
                    reallyHide[index] && (
                      <tr key={index}>
                        <td>{col.label}:</td>
                        <td>
                          {col.display
                            ? col.display(item, query)
                            : (item as any)[col.prop]}
                        </td>
                      </tr>
                    )
                )}
              </tbody>
            </table>
          </td>
        </tr>
      );
    }
  }

  return (
    <div>
      {canHide.some(Boolean) && (
        <div className="btn-toolbar section">
          <button
            type="button"
            className={classNames("btn", "btn-default", fullTable && "active")}
            onClick={() => {
              LocalSettings.set("fullTable", String(!fullTable));
            }}
          >
            Zobraziť celú tabuľku
          </button>
          {!fullTable && (
            <button
              type="button"
              className="btn btn-default"
              onClick={() => setOpen(Array(items.length).fill(!anyOpen))}
            >
              {anyOpen ? "Zabaliť všetky" : "Rozbaliť všetky"}
            </button>
          )}
        </div>
      )}
      <table className={className}>
        <thead>{header}</thead>
        <tbody>{rows}</tbody>
        {!!(footer || message) && (
          <tfoot>
            {!!footer && footer(chosenSize)}
            {!!message && (
              <tr>
                <td colSpan={columns.length - reallyHiddenCount}>{message}</td>
              </tr>
            )}
          </tfoot>
        )}
      </table>
    </div>
  );
}
