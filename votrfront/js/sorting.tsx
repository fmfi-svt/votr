import React, { useContext, useState } from "react";
import _ from "lodash";
import { navigate, QueryContext } from "./router";
import { LocalSettings } from "./LocalSettings";
import { Columns } from "./types";

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

export function sortTable<T>(
  items: T[],
  columns: Columns,
  query: Record<string, string>,
  queryKey: string,
  fullTable?: boolean
): [T[], React.ReactNode] {
  if (columns[0][0]) {
    columns = columns.map(
      ([label, prop, process, preferDesc, hiddenClass]) => ({
        label,
        prop,
        process,
        preferDesc,
        hiddenClass,
      })
    );
  }
  items = items.map((item, index) => ({ ...item, originalIndex: index }));
  var orderString = query[queryKey] || columns.defaultOrder;
  var order = orderString ? orderString.split(/(?=[ad])/) : [];
  var directions = order.map((o) => (o.charAt(0) == "a" ? "asc" : "desc"));
  var iteratees = order.map((o) => {
    var { label, prop, process, preferDesc } = columns[Number(o.substring(1))];
    return (item: T) =>
      (process || _.identity)(prop ? (item as any)[prop] : item);
  });

  items = _.orderBy(items, iteratees, directions);

  function handleClick(event: React.MouseEvent<HTMLElement>) {
    var index = event.currentTarget.getAttribute("data-index");
    var { label, prop, process, preferDesc } = columns[Number(index)];

    var newOrder = _.without(order, "a" + index, "d" + index);
    // prettier-ignore
    newOrder.unshift((
      order[0] == "a" + index ? "d" :
      order[0] == "d" + index ? "a" :
      preferDesc ? "d" : "a") + index);

    navigate({ ...query, [queryKey]: newOrder.join("") });
  }

  var header = (
    <tr>
      {columns.map(
        (
          { label, shortLabel, prop, process, preferDesc, hiddenClass = [] },
          index
        ) => (
          <th
            key={index}
            data-index={index}
            onClick={handleClick}
            className={
              (fullTable ? "" : hiddenClass.join(" ")) +
              " sort " +
              (order[0] == "a" + index
                ? "asc"
                : order[0] == "d" + index
                ? "desc"
                : "")
            }
          >
            {shortLabel ? shortLabel : label}
          </th>
        )
      )}
    </tr>
  );

  return [items, header];
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
  columns: Columns;
  queryKey: string;
  withButtons?: boolean;
  footer?: (fullTable: boolean) => React.ReactNode;
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
      acc.filter(
        (item: string) => !(col.hiddenClass && col.hiddenClass.includes(item))
      ),
    ["hidden-xs", "hidden-sm", "hidden-md", "hidden-lg"]
  );

  function revertHidden(hiddenClass: string[]) {
    const all = ["hidden-xs", "hidden-sm", "hidden-md", "hidden-lg"];
    return all.filter((size) => !hiddenClass.includes(size)).join(" ");
  }

  const rows = [];

  for (const item of sortedItems as (T & { originalIndex: number })[]) {
    rows.push(
      <tr
        key={item.originalIndex}
        onClick={(event) => {
          // Don't toggle the row if we just clicked some link or input in the row.
          var target = event.target as Element;
          if (!target.closest("a, input, button") && !fullTable) {
            toggleInfo(item.originalIndex);
          }
        }}
        className={rowClassName && rowClassName(item)}
      >
        {columns.map(
          (
            {
              label,
              prop,
              process,
              hiddenClass = [],
              cell,
              colProps,
              expansionMark,
            },
            index
          ) => (
            <td
              key={index}
              className={!fullTable ? hiddenClass.join(" ") : ""}
              {...(colProps ? colProps(item) : {})}
            >
              {expansionMark && !fullTable && (
                <span
                  className={`${notExpandable.join(" ")} expand-arrow ${
                    open[item.originalIndex]
                      ? "arrow-expanded"
                      : "arrow-collapsed"
                  }`}
                />
              )}
              {cell ? cell(item, query) : (item as any)[prop]}
            </td>
          )
        )}
      </tr>
    );

    if (!fullTable) {
      rows.push(
        <tr key={`${item.originalIndex}-striped-hack`} className={"hidden"} />
      );

      rows.push(
        <tr
          key={`${item.originalIndex}-info`}
          className={`${notExpandable.join(" ")} ${
            open[item.originalIndex] ? "" : "hidden"
          }`}
        >
          {expandedContentOffset > 0 && <td colSpan={expandedContentOffset} />}
          <td colSpan={columns.length - expandedContentOffset}>
            <table className="table-condensed">
              <tbody>
                {columns
                  .filter((col) => col.hiddenClass)
                  .map((col, index) => (
                    <tr key={index} className={revertHidden(col.hiddenClass)}>
                      <td>{col.label}:</td>
                      <td>
                        {col.cell
                          ? col.cell(item, query)
                          : (item as any)[col.prop]}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </td>
        </tr>
      );
    }
  }

  return (
    <div>
      <div className={`btn-toolbar section ${notExpandable.join(" ")}`}>
        <button
          type="button"
          className={"btn btn-default" + (fullTable ? " active" : "")}
          onClick={() => {
            LocalSettings.set("fullTable", String(!fullTable));
          }}
        >
          Zobraziť celú tabuľku
        </button>
        {!fullTable && (
          <button
            type="button"
            className={"btn btn-default"}
            onClick={() => setOpen(Array(items.length).fill(!anyOpen))}
          >
            {anyOpen ? "Zabaliť všetky" : "Rozbaliť všetky"}
          </button>
        )}
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
}
