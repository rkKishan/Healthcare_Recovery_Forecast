import js from '@eslint/js'
import globals from 'globals'
import react from 'eslint-plugin-react'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'

export default [
  { ignores: ['dist', 'node_modules'] },

  // Config files run in Node, not the browser.
  {
    files: ['*.config.js'],
    languageOptions: {
      globals: globals.node,
      ecmaVersion: 2022,
      sourceType: 'module',
    },
    rules: js.configs.recommended.rules,
  },

  {
    files: ['src/**/*.{js,jsx}'],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
      parserOptions: {
        ecmaFeatures: { jsx: true },
        sourceType: 'module',
      },
    },
    settings: { react: { version: 'detect' } },
    plugins: {
      react,
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      ...js.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,

      // Without these, every component referenced only inside JSX is reported
      // as an unused import.
      'react/jsx-uses-react': 'error',
      'react/jsx-uses-vars': 'error',

      // The dependency-array rules are the ones that catch real bugs here --
      // a stale closure in a data-fetching effect shows the wrong patient's
      // numbers rather than throwing, so it survives manual testing.
      'react-hooks/exhaustive-deps': 'warn',

      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],

      // Unused variables are usually a leftover refactor, but an argument
      // named _ or a caught error deliberately ignored is not.
      'no-unused-vars': ['error', { argsIgnorePattern: '^_', caughtErrors: 'none' }],
    },
  },
]
