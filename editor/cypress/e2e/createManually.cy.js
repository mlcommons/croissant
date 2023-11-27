/// <reference types="cypress" />

import 'cypress-file-upload';
import 'cypress-iframe';


describe('Create a resource manually', () => {
  it('should allow adding a FileObject resource', () => {
    // Streamlit starts on :8501.
    cy.visit('http://localhost:8501')
    cy.get('button').contains('Create').click()
    cy.get('input[aria-label="Name:red[*]"]').type('MyDataset').blur()
    cy.get('[data-testid="stMarkdownContainer"]')
    .contains('Metadata')
    .click()
    cy.get('input[aria-label="URL:red[*]"]').type('https://mydataset.com', {force: true})
    
    // Create a resource manually.
    cy.get('[data-testid="stMarkdownContainer"]').contains('Resources').click()
    cy.get('[data-testid="stMarkdownContainer"]').contains('Add manually').click()

    cy.get('input[aria-label="File name:red[*]"]').type('test.csv').blur()
    cy.get('input[aria-label="SHA256"]').type('abcdefgh1234567').blur()
    cy.get('button').contains('Upload').click()

    // The file is created, so we can click on it to see the details.
    cy.enter('[title="components.tree.tree_component"]').then(getBody => {
      getBody().contains('test.csv').click()
    })

    cy.get('input[aria-label="SHA256:red[*]"]')
        .should('be.disabled')
        .should('have.value', 'abcdefgh1234567')
  })
})
