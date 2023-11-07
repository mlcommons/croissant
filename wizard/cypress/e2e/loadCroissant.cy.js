/// <reference types="cypress" />

import 'cypress-file-upload';

describe('Wizard loads Croissant without Error', () => {
  it('should allow uploading existing croissant files', () => {
    cy.visit('http://localhost:8501')
    cy.get('button').contains('Load').click()

    cy.fixture('titanic.json').then((fileContent) => {
      const file = {
        fileContent,
        fileName: 'titanic.json', mimeType: 'text/json',
      }
      cy.get(
        "[data-testid='stFileUploadDropzone']",
      ).attachFile(file, {
        force: true,
        subjectType: "drag-n-drop",
        events: ["dragenter", "drop"],
      })
    })
    cy.get('[data-testid="stExpander"]')
      .contains('Titanic')
      .should('exist')
    
    cy.get('[data-testid="stException"]').should('not.exist')
  })
})