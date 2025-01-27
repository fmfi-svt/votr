/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/ban-ts-comment, @typescript-eslint/no-floating-promises */

import { type Column, column } from "./sorting";

function columnTypeTest() {
  const plain = column({ label: "" });
  plain satisfies Column<string>;
  plain.display("Hi");

  const prop = column({ label: "", prop: "foo" });
  prop satisfies Column<{ foo: string; bar: RegExp }>;

  const projection = column({
    label: "",
    projection: (item: { foo: string }) => item.foo,
  });
  projection satisfies Column<{ foo: string; bar: RegExp }>;

  // @ts-expect-error
  const customIsError = column({ label: "", custom: "hi" });

  const customPropIsError = column({
    label: "",
    prop: "foo",
    // @ts-expect-error
    custom: 123,
  });

  const displayString = column({
    label: "",
    display: (value: string) => value + value,
  });
  displayString satisfies Column<string>;

  const displayRegExp = column({
    label: "",
    display: (r: RegExp) => r.flags,
  });
  displayRegExp satisfies Column<RegExp>;

  // @ts-expect-error
  const sortKeyRegExpWithoutDisplayIsError = column({
    label: "",
    sortKey: (r: RegExp) => r.flags,
  });

  const displayAndSortKeyConflictIsError = column({
    label: "",
    // @ts-expect-error
    display: (value: string) => value + value,
    sortKey: (value: number) => value + 7,
  });

  // @ts-expect-error
  const projectionRegExpWithoutDisplayIsError = column({
    label: "",
    projection: (item: { foo: RegExp }) => item.foo,
  });

  const projectionRegExp = column({
    label: "",
    projection: (item: { foo: RegExp }) => item.foo,
    display: (r: RegExp) => r.flags,
  });
  projectionRegExp.display({ foo: /a/ });

  const propProjection = column({
    label: "",
    prop: "outer",
    projection: (o: { inner: number }) => o.inner,
  });
  propProjection.display({ outer: { inner: 47 } });

  const propProjectionRegExp = column({
    label: "",
    prop: "outer",
    projection: (o: { inner: RegExp }) => o.inner,
    display: (r: RegExp) => r.flags,
  });
  propProjectionRegExp.display({ outer: { inner: /a/ } });

  const propStringObj: { label: string; prop: string } = {
    label: "",
    prop: "foo",
  };
  // @ts-expect-error
  const propStringIsError = column(propStringObj);

  const fooOrBar: "foo" | "bar" = "foo" as "foo" | "bar";
  const multipleProps = column({ label: "", prop: fooOrBar });
  multipleProps.display({ "foo": 123, "bar": "hi" });
  // @ts-expect-error
  multipleProps.display({ "foo": 123 });
  // @ts-expect-error
  multipleProps.display({ "bar": "hi" });

  const evil1 = { label: "", prop: "foo" };
  const evil2: { label: string } = evil1;
  const evilColumn = column(evil2);
  // It actually behaves like Column<{ foo: string }>, but TypeScript doesn't
  // know about prop. :/
  evilColumn satisfies Column<string>;

  const list = [
    column({ label: "", display: (item: { foo: RegExp }) => "" }),
    column({ label: "", prop: "bar" }),
  ];
  list satisfies Column<{ foo: RegExp; bar: string }>[];
}
