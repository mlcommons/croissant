/// <reference types="cypress" />

import 'cypress-file-upload';
import 'cypress-iframe';


describe('Editor loads a local CSV as a resource', () => {
  it('should display the form: Overview, Metadata, Resources, & Record Sets', () => {
    // Streamlit starts on :8501.
    cy.visit('http://localhost:8501')
    cy.get('button').contains('Create').click()

    cy.get('input[aria-label="Name:red[*]"]').type('MyDataset').blur()
    cy.enter('[title="components.tabs.tabs_component"]').then(getBody => {
      getBody().contains('Metadata').click()
    })
    cy.get('input[aria-label="URL"]').type('https://mydataset.com{enter}')

    cy.enter('[title="components.tabs.tabs_component"]').then(getBody => {
      getBody().contains('Resources').click()
    })
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
    cy.get('button').contains('Upload').click()
    // The file is uploaded, so we can click on it to see the details.
    // Waiting a few seconds to wait for the resource to download.
    cy.wait(2000)
    cy.enter('[title="components.tree.tree_component"]').then(getBody => {
      getBody().find('li').should('be.visible').click()
    })
    // For example, we see the first rows:
    cy.contains('First rows of data:')

    // On the record set page, we see the record set.
    cy.enter('[title="components.tabs.tabs_component"]').then(getBody => {
      getBody().contains('Record Sets').click()
    })
    cy.contains('Generating the dataset...').should('not.exist')
    cy.contains('base.csv_record_set (2 fields)').click()
    // We also see the fields with the proper types.
    cy.get('[data-testid="stDataFrameResizable"]').contains("column1")
    cy.get('[data-testid="stDataFrameResizable"]').contains("Text")
    cy.get('[data-testid="stDataFrameResizable"]').contains("column2")
    cy.get('[data-testid="stDataFrameResizable"]').contains("Integer")

    // I can edit the details of the fields.
    cy.contains('Generating the dataset...').should('not.exist')
    cy.contains('Edit fields details').click()
    cy.get('[data-testid="stExpander"]').last().within(() => {
      cy.get('input[aria-label="Description"]').last().type('This is a nice custom description!{enter}')
    })
    cy.wait(2000)
    cy.get('[data-testid="glide-cell-2-1"]').contains("This is a nice custom description!")
  })
})
