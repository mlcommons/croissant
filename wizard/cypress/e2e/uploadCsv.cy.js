/// <reference types="cypress" />

import 'cypress-file-upload';
import '../support/resize_observer';

describe('Wizard from local CSV', () => {
  it('should display the form: Metadata, Files, & Record Sets', () => {
    cy.ignore_resize_observer()
    // Streamlit starts on :8501.
    cy.visit('http://localhost:8501')
    cy.get('button').contains('Create').click()

    cy.get('input[aria-label="Name:red[*]"]').type('MyDataset').blur()
    cy.get('input[aria-label="URL:red[*]"]').type('https://mydataset.com').blur()
    cy.get('[data-testid="stMarkdownContainer"]').contains('Files').click()
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
  })
  it('should allow uploading existing croissant files', () => {
    cy.ignore_resize_observer()

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
    // at this point if we don't have unhandled errors, we're good, should load into the overview in the future though!
  })
})
