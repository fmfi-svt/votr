import classNames from "classnames";
import { orderBy, range, sum, without } from "lodash-es";
import React, { useContext, useState } from "react";
import { getLocalSetting, setLocalSetting } from "./LocalSettings";
import { ScreenSize, useScreenSize } from "./mediaQueries";
import { navigate, QueryContext } from "./router";
import { Query } from "./types";

export var sortAs = {
  personName: (text: string) => {
    var words = text.replace(/,/g, "").split(" ");
    words = words.filter((word) => !word.match(/\.$/));
    var last = words.pop();
    if (last) words.unshift(last); // move last name to the beginning
    return words.join(" ").toLowerCase();
    // TODO: consider using latinise (see fajr).
  },

  number: (text: string) => {
    return +text.replace(/,/g, ".");
    // TODO: this won't be needed when fladgejt starts returning numbers
  },

  date: (date: string) => {
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

  interval: (text: string) => {
    var index = text.indexOf("do ");
    if (index == -1) return "";
    return sortAs.date(text.substring(index + 3));
  },
};

export interface Column<T> {
  label: React.ReactNode;
  shortLabel: React.ReactNode;
  sortKey: (item: T) => unknown;
  display: (item: T) => React.ReactNode;
  cellProps: (item: T) => React.TdHTMLAttributes<HTMLTableCellElement>;
  expansionMark: boolean;
  preferDesc: boolean;
  hide: (size: ScreenSize) => boolean;
}

export interface ColumnDefinition<K, V, P> {
  label: React.ReactNode;
  shortLabel?: React.ReactNode;
  sortKey?: (value: V) => unknown;
  display?: (value: V) => React.ReactNode;
  cellProps?: (value: V) => React.TdHTMLAttributes<HTMLTableCellElement>;
  expansionMark?: boolean;
  preferDesc?: boolean;
  hide?: (size: ScreenSize) => boolean;
  prop?: K;
  projection?: (item: P) => V;
}

type ColumnDefinitionKeys = keyof ColumnDefinition<unknown, unknown, unknown>;

type InferItem<K extends string, P> = [K] extends [""] ? P : Record<K, P>;

// This is stupid and I'm ashamed of it.
export function column<
  Def extends object,
  K extends string = "",
  V = string | number | null | undefined,
  P = V,
  Item extends InferItem<K, P> = InferItem<K, P>
>(
  input: Def &
    ColumnDefinition<K, V, P> &
    // If V doesn't extend ReactNode, `display` is required.
    (V extends React.ReactNode ? unknown : { display: object }) &
    // If K != "", `prop` is required. (Just a sanity check in case K is
    // manually provided or badly inferred.)
    ([K] extends [""] ? unknown : { prop: K }) &
    // If P != V, `projection` is required. (Just a sanity check in case P is
    // manually provided or badly inferred.)
    (P extends V
      ? V extends P
        ? unknown
        : { projection: object }
      : { projection: object }) &
    // K must not be just string. We want a literal or union of literals.
    ([string] extends [K] ? never : unknown) &
    // Forbid unknown properties on Def.
    Record<Exclude<keyof Def, ColumnDefinitionKeys>, never>
): Column<Item> {
  const {
    label,
    shortLabel = input.label,
    sortKey = (v: V) => v,
    // This `as` should be safe because our type declaration says that if V
    // doesn't extend React.ReactNode, `display` is required.
    display = (v: V) => v as React.ReactNode,
    cellProps = (): React.TdHTMLAttributes<HTMLTableCellElement> => ({}),
    expansionMark = false,
    preferDesc = false,
    hide = () => false,
    prop,
    projection,
  } = input;
  function convert(item: InferItem<K, P>): V {
    // The first `as` is mostly safe, except if `prop` exists at runtime but
    // TypeScript doesn't know about it (e.g. because column() wasn't called
    // with a literal object). :/
    // The second `as` should be safe because if K != "" then `prop` would be
    // required by our type, hence K == "", hence InferItem<K, P> == P.
    const afterProp: P = prop ? (item as Record<K, P>)[prop] : (item as P);
    // The true branch is mostly safe, except if `projection` exists at runtime
    // but TypeScript doesn't know about it (e.g. because column() wasn't called
    // with a literal object). :/
    // The `as` in the false branch should be safe because if P != V then
    // `projection` would be required by our type, hence P == V.
    return projection ? projection(afterProp) : (afterProp as unknown as V);
  }
  return {
    label,
    shortLabel,
    sortKey: (item) => sortKey(convert(item)),
    display: (item) => display(convert(item)),
    cellProps: (item) => cellProps(convert(item)),
    expansionMark,
    preferDesc,
    hide,
  };
}

function getOrder(
  defaultOrder: string | null | undefined,
  query: Query,
  queryKey: string
): string[] {
  var orderString = query[queryKey] || defaultOrder;
  return orderString ? orderString.split(/(?=[ad])/) : [];
}

function sortItems<T>(
  items: T[],
  columns: Column<T>[],
  order: string[]
): number[] {
  var directions = order.map((o) => (o.startsWith("a") ? "asc" : "desc"));
  var iteratees = order.map((o) => {
    const column = columns[Number(o.substring(1))];
    if (!column) return () => "";
    return (originalIndex: number) => column.sortKey(items[originalIndex]!);
  });
  return orderBy(range(items.length), iteratees, directions);
}

function renderHeader<T>(
  columns: Column<T>[],
  query: Query,
  queryKey: string,
  order: string[],
  reallyHide: boolean[]
): React.ReactNode {
  return (
    <tr>
      {columns.map(({ shortLabel, preferDesc }, index) => {
        const strA = `a${index}`;
        const strD = `d${index}`;

        function handleClick() {
          var newOrder = without(order, strA, strD);
          // prettier-ignore
          newOrder.unshift(
            order[0] == strA ? strD :
            order[0] == strD ? strA :
            preferDesc ? strD : strA);

          navigate({ ...query, [queryKey]: newOrder.join("") });
        }

        if (reallyHide[index]) return null;

        return (
          <th
            key={index}
            onClick={handleClick}
            className={classNames(
              "sort",
              order[0] == strA && "asc",
              order[0] == strD && "desc"
            )}
          >
            {shortLabel}
          </th>
        );
      })}
    </tr>
  );
}

export function SortableTable<T>({
  items,
  columns,
  defaultOrder,
  queryKey,
  withButtons,
  footer,
  message,
  rowClassName,
  expandedContentOffset = 0,
}: {
  items: T[];
  columns: Column<T>[];
  defaultOrder?: string;
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

  var fullTable = getLocalSetting("fullTable") == "true";

  var order = getOrder(defaultOrder, query, queryKey);

  var sortedIndexes = sortItems(items, columns, order);

  var deviceSize = useScreenSize();

  var chosenSize = fullTable ? ScreenSize.LG : deviceSize;

  var canHide = columns.map((column) => column.hide(deviceSize));
  var reallyHide = canHide.map((canHideColumn) => canHideColumn && !fullTable);
  var reallyHiddenCount = sum(reallyHide);

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
        className={rowClassName?.(item)}
      >
        {columns.map(
          ({ display, cellProps, expansionMark }, index) =>
            !reallyHide[index] && (
              <td key={index} {...cellProps(item)}>
                {expansionMark && !!reallyHiddenCount && (
                  <span
                    className={classNames(
                      "expand-arrow",
                      open[originalIndex] ? "arrow-expanded" : "arrow-collapsed"
                    )}
                  />
                )}
                {display(item)}
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
                  ({ label, display }, index) =>
                    reallyHide[index] && (
                      <tr key={index}>
                        <td>{label}:</td>
                        <td>{display(item)}</td>
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
              setLocalSetting("fullTable", String(!fullTable));
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
