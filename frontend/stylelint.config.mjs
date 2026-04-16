// @see: https://stylelint.io

export default {
  root: true,
  // Extend shared presets
  extends: [
    'stylelint-config-standard', // Base CSS rules
    'stylelint-config-html/vue', // Vue SFC <style>
    'stylelint-config-standard-scss', // SCSS
    'stylelint-config-recommended-vue/scss', // Vue + SCSS
    'stylelint-config-recess-order', // Property order
  ],
  overrides: [
    // Lint <style> in .vue/.html via postcss-html
    {
      files: ['**/*.{vue,html}'],
      customSyntax: 'postcss-html',
    },
  ],
  rules: {
    'function-url-quotes': 'always', // always | never for url() quotes
    'color-hex-length': 'long', // short | long hex colors
    'rule-empty-line-before': 'never', // blank line before rules
    'font-family-no-missing-generic-family-keyword': true, // require generic font family
    // 'scss/at-import-partial-extension': null, // allow @import of partials without extension
    'property-no-unknown': null, // allow unknown properties (framework tokens)
    'no-empty-source': null, // allow empty style blocks
    'selector-class-pattern': null, // class naming pattern
    'value-no-vendor-prefix': null, // allow -webkit- etc. (e.g. line-clamp)
    'no-descending-specificity': null, // specificity ordering overrides
    'value-keyword-case': null, // v-bind() and SCSS keyword casing
    'selector-pseudo-class-no-unknown': [
      true,
      {
        ignorePseudoClasses: ['global', 'v-deep', 'deep'],
      },
    ],
  },
  ignoreFiles: ['**/*.js', '**/*.jsx', '**/*.tsx', '**/*.ts', 'node_modules', 'dist', 'public', 'stats.html'],
}
