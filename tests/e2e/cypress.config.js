const { defineConfig } = require('cypress')

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://localhost:5173',
    supportFile: false,
    specPattern: 'tests/e2e/specs/**/*.cy.js',
    video: false,
    screenshotOnRunFailure: true,
  },
})
