/// <reference types="cypress" />

import 'cypress-file-upload';

describe('load existing errored croissant', () => {
  it('should display errors', () => {
    cy.visit('http://localhost:8501')

    cy.fixture('coco.json').then((fileContent) => {
      const file = {
        fileContent,
        fileName: 'coco.json', mimeType: 'text/json',
      }
      cy.get(
        "[data-testid='stFileUploadDropzone']",
      ).attachFile(file, {
        force: true,
        subjectType: "drag-n-drop",
        events: ["dragenter", "drop"],
      })
    })
    cy.get('[data-testid="stMarkdownContainer"]').contains("Errors").should('not.exist')
    // Empty the `name` field to create an error:
    cy.get('[data-testid="stMarkdownContainer"]').contains('RecordSets').click()
    cy.contains('split_enums (2 fields)').click()
    cy.get('input[aria-label="Name:red[*]"][value="split_enums"]').should('be.visible').type('{selectall}{backspace}{enter}')
    cy.get('[data-testid="stMarkdownContainer"]').contains('Overview').click()
    cy.get('[data-testid="stMarkdownContainer"]').contains("Errors").should('exist')
  })
})