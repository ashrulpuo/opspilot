// @see: https://cz-git.qbenben.com/zh/guide
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

// Create equivalents for __dirname and __filename
const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const scopes = fs
  .readdirSync(path.resolve(__dirname, 'src'), { withFileTypes: true })
  .filter(dirent => dirent.isDirectory())
  .map(dirent => dirent.name.replace(/s$/, ''))

/** @type {import('cz-git').UserConfig} */
export default {
  ignores: [commit => commit.includes('init')],
  extends: ['@commitlint/config-conventional'],
  rules: {
    // @see: https://commitlint.js.org/#/reference-rules
    'body-leading-blank': [2, 'always'],
    'footer-leading-blank': [1, 'always'],
    'header-max-length': [2, 'always', 108],
    'subject-empty': [2, 'never'],
    'type-empty': [2, 'never'],
    'subject-case': [0],
    'type-enum': [
      2,
      'always',
      [
        'feat',
        'i18n',
        'fix',
        'docs',
        'style',
        'refactor',
        'perf',
        'test',
        'build',
        'ci',
        'chore',
        'revert',
        'wip',
        'workflow',
        'types',
        'release',
      ],
    ],
  },
  prompt: {
    messages: {
      type: "Select the type of change that you're committing:",
      scope: 'Denote the SCOPE of this change (optional):',
      customScope: 'Denote the SCOPE of this change:',
      subject: 'Write a SHORT, IMPERATIVE tense description of the change:\n',
      body: 'Provide a LONGER description of the change (optional). Use "|" to break new line:\n',
      breaking: 'List any BREAKING CHANGES (optional). Use "|" to break new line:\n',
      footerPrefixsSelect: 'Select the ISSUES type of changeList by this change (optional):',
      customFooterPrefixs: 'Input ISSUES prefix:',
      footer: 'List any ISSUES by this change. E.g.: #31, #34:\n',
      confirmCommit: 'Are you sure you want to proceed with the commit above?',
    },
    types: [
      {
        value: 'feat',
        name: 'feat:     🚀  A new feature',
        emoji: '🚀',
      },
      {
        value: 'fix',
        name: 'fix:      🧩  A bug fix',
        emoji: '🧩',
      },
      {
        value: 'docs',
        name: 'docs:     📚  Documentation only changes',
        emoji: '📚',
      },
      {
        value: 'style',
        name: 'style:    🎨  Changes that do not affect the meaning of the code',
        emoji: '🎨',
      },
      {
        value: 'refactor',
        name: 'refactor: ♻️   A code change that neither fixes a bug nor adds a feature',
        emoji: '♻️',
      },
      {
        value: 'perf',
        name: 'perf:     ⚡️  A code change that improves performance',
        emoji: '⚡️',
      },
      {
        value: 'test',
        name: 'test:     ✅  Adding missing tests or correcting existing tests',
        emoji: '✅',
      },
      {
        value: 'build',
        name: 'build:    📦️   Changes that affect the build system or external dependencies',
        emoji: '📦️',
      },
      {
        value: 'ci',
        name: 'ci:       🎡  Changes to our CI configuration files and scripts',
        emoji: '🎡',
      },
      {
        value: 'chore',
        name: "chore:    🔨  Other changes that don't modify src or test files",
        emoji: '🔨',
      },
      {
        value: 'revert',
        name: 'revert:   ⏪️  Reverts a previous commit',
        emoji: '⏪️',
      },
      {
        value: 'wip',
        name: 'wip:      🕔  work in process',
        emoji: '🕔',
      },
      {
        value: 'workflow',
        name: 'workflow: 📋  workflow improvements',
        emoji: '📋',
      },
      {
        value: 'type',
        name: 'type:     🔰  type definition file changes',
        emoji: '🔰',
      },
    ],
    useEmoji: true,
    scopes: [...scopes],
    customScopesAlign: 'bottom',
    emptyScopesAlias: 'empty',
    customScopesAlias: 'custom',
    allowBreakingChanges: ['feat', 'fix'],
  },
}
