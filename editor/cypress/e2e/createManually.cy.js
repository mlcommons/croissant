/// <reference types="cypress" />

import 'cypress-file-upload';
import 'cypress-iframe';


describe('Create a resource manually', () => {
  it('should allow adding a FileObject resource', () => {
    // Streamlit starts on :8501.
    cy.visit('http://localhost:8501')
    cy.get('button').contains('Create').click()
    cy.get('input[aria-label="Name:red[*]"]').type('MyDataset{enter}')
    cy.get('input[aria-label="URL:red[*]"]').type('https://mydataset.com{enter}', {force: true})
    cy.contains("Croissant files are composed of three layers:")
    cy.enter('[title="components.tabs.tabs_component"]').then(getBody => {
      getBody().contains('Metadata').click()
    })
    
    // Create a resource manually.
    cy.enter('[title="components.tabs.tabs_component"]').then(getBody => {
      getBody().contains('Resources').click()
    })
    cy.get('[data-testid="stMarkdownContainer"]').contains('Add manually').click()
    cy.get('button').contains('Upload').click()


    // The file is created, so we can click on it to see the details.
    cy.enter('[title="components.tree.tree_component"]').then(getBody => {
      getBody().contains('file_object').click()
    })
    // We can edit it
    cy.get('input[aria-label="Name:red[*]"]').type('{selectall}{backspace}test.csv{enter}')
    cy.wait(1000)
    cy.enter('[title="components.tree.tree_component"]').then(getBody => {
      getBody().contains('test.csv').click()
    })
    cy.get('input[aria-label="SHA256:red[*]"]').type('abcdefgh1234567{enter}')

    cy.get('input[aria-label="SHA256:red[*]"]')
        .should('have.value', 'abcdefgh1234567')
  })
})
