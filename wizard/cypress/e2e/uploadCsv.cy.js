/// <reference types="cypress" />

import 'cypress-file-upload';

describe('Wizard from local CSV', () => {
  it('should display the form: Overview, Metadata, Resources, & Record Sets', () => {
    // Streamlit starts on :8501.
    cy.visit('http://localhost:8501')
    cy.get('button').contains('Create').click()

    cy.get('[data-testid="stMarkdownContainer"]')
      .contains('Metadata')
      .click()
    cy.get('input[aria-label="Name:red[*]"]').type('MyDataset').blur()
    cy.get('input[aria-label="URL:red[*]"]').type('https://mydataset.com', {force: true})

    cy.get('[data-testid="stMarkdownContainer"]').contains('Resources').click()
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
    // The file is uploaded, so we see its hash:
    cy.contains('c2896706e40a3dc4ee012dfe69c9a43ab592fc8c625b83760d1bb1042160a01c')
  })
})
