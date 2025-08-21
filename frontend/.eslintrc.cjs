/* eslint-env node */
require('@rushstack/eslint-patch/modern-module-resolution')

module.exports = {
  root: true,
  'extends': [
    'plugin:vue/vue3-essential',
    'eslint:recommended',
    '@vue/eslint-config-typescript',
    '@vue/eslint-config-prettier/skip-formatting'
  ],
  parserOptions: {
    ecmaVersion: 'latest'
  },
  env: {
    node: true,
  },
  rules: {
    // Vue specific rules
    'vue/multi-word-component-names': 'off',
    'vue/no-unused-vars': 'error',

    // General rules
    'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    'prefer-const': 'error',
    'no-unused-vars': 'off', // Let TypeScript handle this
  },
  overrides: [
    {
      files: ['*.config.js', '*.config.ts'],
      env: {
        node: true,
      },
    },
  ],
}
