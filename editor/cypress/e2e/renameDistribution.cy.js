/// <reference types="cypress" />

import 'cypress-file-upload';
import 'cypress-iframe';


describe('Renaming of FileObjects/FileSets/RecordSets/Fields.', () => {
  it('should rename the FileObject/FileSet everywhere', () => {
    cy.visit('http://localhost:8501')

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
    cy.get('button').contains('Resources').click()
    cy.enter('[title="components.tree.tree_component"]').then(getBody => {
      // Click on genders.csv
      getBody().contains('genders.csv').click()
    })
    cy.get('input[aria-label="Name:red[*]"][value="genders.csv"]').type('{selectall}{backspace}the-new-name{enter}')

    cy.get('button').contains('RecordSets').click()
    cy.contains('genders').click()
    cy.contains('Edit fields details').click()
    cy.contains('the-new-name')
  })
})
