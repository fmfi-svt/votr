/* eslint-disable no-var */

import { VotrVar } from "./types";

export {};

declare global {
  var Votr: VotrVar;
  var ga: ((...args: unknown[]) => void) | undefined;
  var process: { env: { NODE_ENV: unknown } };
}

// How does this file work?
//
// `tsc` loads all files configured in tsconfig "files" or "includes", and
// anything they import. They are compiled together as a single project.
//
// webpack's ts-loader also loads them all. Not just the webpack entry point(s).
// (Exception: if you enable "onlyCompileBundledFiles" (which we don't), it
// would only read the entry point plus all .d.ts files.)
//
// If `tsc` loads a non-module file (containing no `import` or `export`), its
// declared variables and types become globally visible to all other files
// loaded by `tsc`, without any import.
//
// Module files can contain `declare global` blocks which work the same way:
// globally visible without any import. Also, vars in `declare global` can be
// used with and without the `window.` prefix.
//
// So it doesn't matter that this file isn't imported anywhere. This works for
// any file name and any extension, both ".ts" and ".d.ts".
//
// https://basarat.gitbook.io/typescript/project/modules
// https://stackoverflow.com/questions/55890481/does-globals-d-ts-have-a-special-meaning-in-typescript
