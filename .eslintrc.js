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
        "plugin:@typescript-eslint/strict-type-checked",
        "plugin:@typescript-eslint/stylistic-type-checked",
        "plugin:compat/recommended",
        "plugin:escompat/recommended",
        "plugin:escompat/typescript-" + tstarget,
        "plugin:@eslint-react/recommended-type-checked-legacy",
        "plugin:react-hooks/recommended",
      ],
      "overrides": [],
      "parser": "@typescript-eslint/parser",
      "parserOptions": {
        "ecmaVersion": "latest",
        "sourceType": "module",
        "projectService": true,
        "tsconfigRootDir": __dirname,
      },
      "rules": {
        // Good rules.
        "curly": ["warn", "multi-line"],

        // Nice to have. Not too valuable, but not too bothersome. We can remove
        // them if they cause trouble later.
        "@eslint-react/naming-convention/component-name": "warn",
        "@eslint-react/naming-convention/use-state": "warn",
        "@eslint-react/no-children-prop": "warn",
        "@eslint-react/no-missing-component-display-name": "warn",
        "@eslint-react/no-unused-class-component-members": "warn",
        "@eslint-react/hooks-extra/no-unnecessary-use-callback": "warn",
        "@eslint-react/hooks-extra/no-unnecessary-use-memo": "warn",
        "@typescript-eslint/default-param-last": "warn",
        "@typescript-eslint/no-dupe-class-members": "warn",
        "@typescript-eslint/no-invalid-this": "warn",
        "@typescript-eslint/no-loop-func": "warn",
        "@typescript-eslint/no-redeclare": "warn",
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
        "symbol-description": "warn",
        "yoda": "warn",

        "no-restricted-syntax": [
          "error",
          {
            "selector":
              "MemberExpression[object.name='Date'][property.name='now']",
            "message": "Remember to use getMsecNow() instead of Date.now()",
          },
          {
            "selector": "NewExpression[callee.name='Date'][arguments.length=0]",
            "message": "Remember to use getDateNow() instead of new Date()",
          },
        ],

        // I slightly dislike the changes proposed by this rule. For now let's
        // at least disable it for function parameters.
        "@typescript-eslint/no-inferrable-types": [
          "error",
          { "ignoreParameters": true },
        ],

        // Too annoying with default options.
        "@typescript-eslint/no-confusing-void-expression": [
          "error",
          { "ignoreArrowShorthand": true },
        ],

        // Too annoying with default options. The docs warn that you should use
        // toFixed() or toPrecision() with floats, but Votr only uses integers.
        "@typescript-eslint/restrict-template-expressions": [
          "error",
          { "allowNumber": true },
        ],

        // TODO: Maybe enable later.
        "@typescript-eslint/no-deprecated": "off",
        "@typescript-eslint/prefer-regexp-exec": "off",

        // Many false positives and almost no true positives.
        "@typescript-eslint/prefer-nullish-coalescing": "off",

        // What a pointless rule. Both postfix `!` and `eslint-disable-line` are
        // assertions that mean "trust me, I know what I'm doing". Why lock one
        // of them behind the other?
        "@typescript-eslint/no-non-null-assertion": "off",

        // Good idea per se, but Votr often has a good reason to do it.
        "@eslint-react/no-array-index-key": "off",

        // I don't think "no-shadow" is useful enough to enable permanently, but
        // you can occasionally try it with:
        //   yarn eslint . --rule '{"@typescript-eslint/no-shadow":"warn"}'
      },
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
