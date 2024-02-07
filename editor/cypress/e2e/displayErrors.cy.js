/// <reference types="cypress" />

import 'cypress-file-upload';
import 'cypress-iframe';

import {VERSIONS} from '../support/constants';

VERSIONS.forEach(version => {
  const fixture = `${version}/coco.json`
  describe(`[Version ${version}] load existing errored croissant`, () => {
    it('should display errors', () => {
      cy.visit('http://localhost:8501')
      cy.fixture(fixture).then((fileContent) => {
        const file = {
          fileContent,
          fileName: fixture,
          mimeType: 'text/json',
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
      cy.enter('[title="components.tabs.tabs_component"]').then(getBody => {
        getBody().contains('Record Sets').click()
      })
      cy.contains('annotations (4 fields)')
      cy.contains('split_enums (2 fields)').click()
      cy.contains('Generating the dataset...').should('not.exist')
      cy.get('input[aria-label="Name:red[*]"][value="split_enums"]').should('be.visible').type('{selectall}{backspace}{enter}')
      cy.wait(2000)
      cy.contains('Generating the dataset...').should('not.exist')
      cy.enter('[title="components.tabs.tabs_component"]').then(getBody => {
        getBody().contains('Overview').click({force: true})
      })
      cy.get('[data-testid="stMarkdownContainer"]').contains("Errors").should('exist')
    })
  })
})
