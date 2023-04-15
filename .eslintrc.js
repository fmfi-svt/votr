const fs = require("fs");

// Read "target" from tsconfig.json. require("./tsconfig.json") and
// JSON.parse(tsconfig) won't work because it contains comments.
const tsconfig = fs.readFileSync(__dirname + "/tsconfig.json", "utf8");
const tstarget = tsconfig.match(/"target": "es(\d\d\d\d)"/)[1];

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
        "plugin:compat/recommended",
        "plugin:escompat/recommended",
        "plugin:escompat/typescript-" + tstarget,
        "plugin:react/recommended",
        "plugin:react-hooks/recommended",
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
        // Good rules.
        "curly": ["warn", "multi-line"],
        "react/button-has-type": "error",

        // Nice to have. Not too valuable, but not too bothersome. We can remove
        // them if they cause trouble later.
        "@typescript-eslint/default-param-last": "warn",
        "@typescript-eslint/no-dupe-class-members": "warn",
        "@typescript-eslint/no-duplicate-type-constituents": "warn",
        "@typescript-eslint/no-invalid-this": "warn",
        "@typescript-eslint/no-loop-func": "warn",
        "@typescript-eslint/no-redeclare": "warn",
        "@typescript-eslint/no-redundant-type-constituents": "warn",
        "@typescript-eslint/no-unused-expressions": "warn",
        "@typescript-eslint/require-array-sort-compare": "warn",
        "accessor-pairs": "warn",
        "block-scoped-var": "warn",
        "consistent-return": "warn",
        "default-case-last": "warn",
        "default-case": "warn",
        "eqeqeq": "off", // TODO: Maybe enable later; maybe { "null": "ignore" }
        "grouped-accessor-pairs": "warn",
        "lines-between-class-members": "warn",
        "logical-assignment-operators": "warn",
        "new-cap": "warn",
        "no-await-in-loop": "warn",
        "no-bitwise": "warn",
        "no-caller": "warn",
        "no-constant-binary-expression": "warn",
        "no-eval": "warn",
        "no-extend-native": "warn",
        "no-extra-bind": "warn",
        "no-extra-label": "warn",
        "no-label-var": "warn",
        "no-lone-blocks": "warn",
        "no-multi-str": "warn",
        "no-new-func": "warn",
        "no-new-object": "warn",
        "no-new-wrappers": "warn",
        "no-octal-escape": "warn",
        "no-param-reassign": ["warn", { "props": true }],
        "no-promise-executor-return": "warn",
        "no-return-assign": "warn",
        "no-self-compare": "warn",
        "no-sequences": ["warn", { "allowInParentheses": false }],
        "no-template-curly-in-string": "warn",
        "no-underscore-dangle": "warn",
        "no-unmodified-loop-condition": "warn",
        "no-unneeded-ternary": ["warn", { "defaultAssignment": false }],
        "no-unreachable-loop": "warn",
        "no-useless-call": "warn",
        "no-useless-computed-key": "warn",
        "no-useless-concat": "warn",
        "no-useless-rename": "warn",
        "no-useless-return": "warn",
        "no-void": "warn",
        "operator-assignment": "warn",
        "prefer-arrow-callback": "warn",
        "prefer-numeric-literals": "warn",
        "prefer-object-spread": "warn",
        "prefer-promise-reject-errors": "warn",
        "react/function-component-definition": "warn",
        "react/jsx-fragments": ["warn", "element"],
        "react/jsx-no-constructed-context-values": "warn",
        "react/jsx-no-useless-fragment": "warn",
        "react/jsx-pascal-case": "warn",
        "react/no-namespace": "warn",
        "symbol-description": "warn",
        "yoda": "warn",

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

        // I don't think "no-shadow" is useful enough to enable permanently, but
        // you can occasionally try it with:
        //   yarn eslint . --rule '{"@typescript-eslint/no-shadow":"warn"}'
      },
      "settings": { "react": { "version": "detect" } },
    },
    {
      "files": ["*.js"],
      "env": { "node": true },
      "parserOptions": { "ecmaVersion": "latest" },
    },
  ],
  "ignorePatterns": ["*.tmp*", "*env*/", "docs/_build", "static", "var"],
  "reportUnusedDisableDirectives": true,
};
