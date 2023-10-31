/// <reference types="cypress" />

import 'cypress-file-upload';

describe('Wizard from local CSV', () => {
  it('should display the form: Metadata > Files', () => {
    // Streamlit starts on :8501.
    cy.visit('http://localhost:8501')
    cy.get('button').contains('Create').click()
    cy.get('.stCodeBlock').contains('{}')

    cy.get('input[aria-label="Name:red[*]"]').type('MyDataset').blur()
    cy.get('input[aria-label="URL:red[*]"]').type('https://mydataset.com').blur()
    cy.get('button').contains('Next').click()

    // Add the local CSV file by drag and drop.
    cy.get('[data-testid="stCheckbox"]').click()
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
    cy.get('[data-testid="stMarkdownContainer"]').contains('Submit').click()
    cy.get('[data-testid="stJson"]').should('contain', '@context')
  })
})
