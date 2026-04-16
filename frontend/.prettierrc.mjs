// @see: https://prettier.io/docs/options

export default {
  // Max line length before wrapping
  printWidth: 120,
  // Spaces per indent level
  tabWidth: 2,
  // Use spaces instead of tabs
  useTabs: false,
  // Omit semicolons
  semi: false,
  // Prefer single quotes in JS/TS
  singleQuote: true,
  // Quote object keys only when needed
  quoteProps: 'as-needed',
  // Use double quotes in JSX (common React/Vue style)
  jsxSingleQuote: false,
  // Trailing commas where valid in ES5
  trailingComma: 'es5',
  // Spaces inside { foo: bar }
  bracketSpacing: true,
  // Put `>` of multiline JSX on its own line
  bracketSameLine: false,
  // Omit parens when arrow has one param
  arrowParens: 'avoid',
  requirePragma: false,
  insertPragma: false,
  // Do not reflow markdown prose
  proseWrap: 'preserve',
  // How HTML whitespace affects wrapping: css | strict | ignore
  htmlWhitespaceSensitivity: 'css',
  // Do not extra-indent <script>/<style> in Vue SFCs
  vueIndentScriptAndStyle: false,
  // Line endings: lf | crlf | cr | auto
  endOfLine: 'lf',
  rangeStart: 0,
  rangeEnd: Infinity,
}
