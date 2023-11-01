/// <reference types="cypress" />

import 'cypress-file-upload';

describe('Wizard from local CSV', () => {
  it('should display the form: Metadata, Files, & Record Sets', () => {
    const resizeObserverLoopErrRe = /^ResizeObserver loop limit exceeded/

    // consensus was that this exception didn't matter mostly, and was intermittent when running tests.
    Cypress.on('uncaught:exception', err => {
      if (resizeObserverLoopErrRe.test(err.message)) {
        return false
      }
      throw new Error("'" + err.message + "'")
    })
    // Streamlit starts on :8501.
    cy.visit('http://localhost:8501')
    cy.get('button').contains('Create').click()

    cy.get('input[aria-label="Name:red[*]"]').type('MyDataset').blur()
    cy.get('input[aria-label="URL:red[*]"]').type('https://mydataset.com').blur()
    cy.get('[data-testid="stMarkdownContainer"]').contains('Files').click()
    // Drag and drop mimicking: streamlit/e2e/specs/st_file_uploader.spec.js.
    cy.fixture('base.csv').then((fileContent) => {
      const file = {
        fileContent,
        fileName: 'base.csv', mimeType: 'text/csv',
      }
      cy.get(
        "[data-testid='stFileUploadDropzone']",
      ).attachFile(file, {
        force: true,
        subjectType: "drag-n-drop",
        events: ["dragenter", "drop"],
      })
    })
    cy.get('.uploadedFileData').contains('base.csv')
    cy.get('button').contains('Add').click()
  })
})
