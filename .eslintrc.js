module.exports = {
  "extends": ["eslint:recommended"],
  // Using "overrides" here because "yarn eslint ." also runs on .eslintrc.js
  // and webpack.config.js, but typescript-eslint complained about them. Sigh.
  "overrides": [
    {
      "files": ["**/*.ts", "**/*.tsx"],
      "extends": [
        "eslint:recommended",
        "plugin:@typescript-eslint/recommended",
        "plugin:@typescript-eslint/recommended-requiring-type-checking",
        "plugin:@typescript-eslint/strict",
      ],
      "overrides": [],
      "parser": "@typescript-eslint/parser",
      "parserOptions": {
        "ecmaVersion": "latest",
        "sourceType": "module",
        "project": true,
        "tsconfigRootDir": __dirname,
      },
      "rules": {
        // We still use var everywhere. Maybe we'll enable no-var later.
        //
        // It's not in eslint:recommended, but typescript-eslint enables it at
        // https://github.com/typescript-eslint/typescript-eslint/blob/main/packages/eslint-plugin/src/configs/eslint-recommended.ts
        // with comment: "ts transpiles let/const to var, so no need for vars any more"
        "no-var": "off",

        // I slightly dislike the changes proposed by this rule. For now let's
        // at least disable it for function parameters.
        "@typescript-eslint/no-inferrable-types": [
          "error",
          { "ignoreParameters": true },
        ],

        // Many false positives and almost no true positives.
        "@typescript-eslint/prefer-nullish-coalescing": "off",

        // What a pointless rule. Both postfix `!` and `eslint-disable-line` are
        // assertions that mean "trust me, I know what I'm doing". Why lock one
        // of them behind the other?
        "@typescript-eslint/no-non-null-assertion": "off",
      },
    },
    {
      "files": ["*.js"],
      "env": { "node": true },
      "parserOptions": { "ecmaVersion": "latest" },
    },
  ],
  "ignorePatterns": ["*env*/**", "votrfront/static/**"],
  "reportUnusedDisableDirectives": true,
};
