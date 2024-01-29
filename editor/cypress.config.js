const { defineConfig } = require("cypress");

module.exports = defineConfig({
  // To access content within Streamlit iframes for custom components:
  chromeWebSecurity: false,
  defaultCommandTimeout: 20000,
  e2e: {},
});
