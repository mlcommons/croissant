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
    cy.get('[data-testid="stMarkdownContainer"]').contains("Errors").should('exist')
  })
})