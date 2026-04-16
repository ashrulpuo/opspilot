// https://eslint.nodejs.cn/docs/latest/use/configure/configuration-files

import globals from 'globals'
import js from '@eslint/js'
import vue from 'eslint-plugin-vue'
import tseslint from 'typescript-eslint'
import prettier from 'eslint-plugin-prettier'

// ESLint globals from Vite auto-import
import fs from 'fs'
const autoImportConfig = JSON.parse(fs.readFileSync('.eslintrc-auto-import.json', 'utf-8'))

/** @type {import('eslint').Linter.Config[]} */

// Global types for Vue SFC / app
const GlobalType = {
  ...autoImportConfig.globals,
  ...globals.browser,
  ...globals.node,
  NodeJS: true,
  PageQuery: 'readonly',
  PageResult: 'readonly',
  OptionTreeType: 'readonly',
  SelectOption: 'readonly',
  ResponseData: 'readonly',
  ExcelResult: 'readonly',
  TagView: 'readonly',
  AppSettings: 'readonly',
  __APP_INFO__: 'readonly',
  NullableString: 'readonly',
  TreeLike: 'readonly',
  FileType: 'readonly',
  IObject: 'readonly',
  // Canvas API globals
  CanvasTextBaseline: 'readonly',
  CanvasRenderingContext2D: 'readonly',
  HTMLCanvasElement: 'readonly',
  Menu: 'readonly',
  ExcelMimeType: 'readonly',
  ImageMimeType: 'readonly',
  MetaProps: 'readonly',
  MenuOptions: 'readonly',
}

export default [
  // Ignore patterns
  {
    ignores: [
      '*.d.ts',
      '**/coverage',
      '**/dist',
      'vite.config.ts',
      'mock/**',
      'src/types/**',
      'webhook-receivers/**', // Generated webhook receiver stubs
      'tmp/**',
      'scripts/**',
    ],
  },

  // JavaScript recommended
  js.configs.recommended,

  // TypeScript recommended
  ...tseslint.configs.recommended,

  // Vue recommended
  ...vue.configs['flat/recommended'],

  // Shared rules for JS/TS/Vue
  {
    files: ['**/*.{js,mjs,cjs,ts,tsx,vue}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: GlobalType,
      parserOptions: {
        parser: tseslint.parser,
        ecmaVersion: 'latest',
        sourceType: 'module',
      },
    },
    plugins: {
      prettier,
      '@typescript-eslint': tseslint.plugin,
      vue,
    },
    rules: {
      // Prettier
      'prettier/prettier': 'error',

      // Blank lines
      'no-multiple-empty-lines': ['error', { max: 1, maxBOF: 0, maxEOF: 0 }],

      // TypeScript
      '@typescript-eslint/consistent-type-imports': 'error',
      '@typescript-eslint/no-unused-expressions': 'off',
      '@typescript-eslint/no-unused-vars': 'off',
      '@typescript-eslint/no-explicit-any': 'off',

      // Vue
      'vue/multi-word-component-names': 'off',
      'vue/max-attributes-per-line': 'off',
      'vue/html-self-closing': 'off',
      'vue/html-indent': 'off',
      'vue/singleline-html-element-content-newline': 'off',
      'vue/component-name-in-template-casing': 'off',
      'vue/require-default-prop': 'off',
      'vue/html-closing-bracket-newline': 'off',

      // General
      curly: ['error', 'all'],
      'no-console': ['error', { allow: ['error'] }],
      'no-debugger': 'error',
      'no-unused-vars': [
        'error',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^[A-Z0-9_]+$',
          caughtErrors: 'none',
          ignoreRestSiblings: true,
        },
      ],
    },
  },

  // Vue SFC parser
  {
    files: ['**/*.vue'],
    languageOptions: {
      parser: vue.parser,
      parserOptions: {
        jsx: true,
        parser: tseslint.parser,
        ecmaVersion: 'latest',
        sourceType: 'module',
        extraFileExtensions: ['.vue'],
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
  },

  // TypeScript project rules
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
        project: './tsconfig.json',
      },
    },
    rules: {
      '@typescript-eslint/no-floating-promises': 'error',
      '@typescript-eslint/await-thenable': 'error',
      '@typescript-eslint/no-misused-promises': 'error',
    },
  },
]
