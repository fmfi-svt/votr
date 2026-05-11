/* eslint-disable no-var */

declare module "*.scss" {}

declare var Votr: import("./types").VotrVar;

declare var ga: ((...args: unknown[]) => void) | undefined;

declare var process: { env: { NODE_ENV: unknown } };

// How does this file work?
//
// `tsc` loads all files configured in tsconfig "files" or "includes", and
// anything they import. They are compiled together as a single project.
//
// webpack's ts-loader also loads them all. Not just the webpack entry point(s).
// (Exception: if you enable "onlyCompileBundledFiles" (which we don't), it
// would only read the entry point plus all .d.ts files.)
//
// If `tsc` loads a non-module file (i.e. containing no top-level `import` or
// `export` statement), its declared variables and types become globally visible
// to all other files loaded by `tsc`, without any import. In particular, `var`
// can be used with and without the `window.` prefix.
//
// So it doesn't matter that this file isn't imported anywhere. This works for
// any file name and any extension, both ".ts" and ".d.ts".
//
// Module files can contain `declare global` blocks which work similarly. But
// they cannot contain "ambient module declarations" such as `declare module
// "*.scss"`. So this has to be a script, not a module.
//
// https://basarat.gitbook.io/typescript/project/modules
// https://stackoverflow.com/questions/55890481/does-globals-d-ts-have-a-special-meaning-in-typescript
// https://www.typescriptlang.org/docs/handbook/modules/reference.html
