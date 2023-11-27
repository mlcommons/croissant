const { defineConfig } = require("cypress");

module.exports = defineConfig({
  // To access content within Streamlit iframes for custom components:
  chromeWebSecurity: false,
  defaultCommandTimeout: 10000,
  e2e: {},
});
