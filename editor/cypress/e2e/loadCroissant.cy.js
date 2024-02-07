/// <reference types="cypress" />

import "cypress-file-upload";
import "cypress-iframe";
import * as path from "path";

import { VERSIONS } from "../support/constants";

VERSIONS.forEach((version) => {
  const fixture = `${version}/titanic.json`;
  describe(`[Version ${version}] Editor loads Croissant without Error`, () => {
    it("should allow uploading existing croissant files", () => {
      cy.visit("http://localhost:8501");
      cy.fixture(fixture).then((fileContent) => {
        const file = {
          fileContent,
          fileName: fixture,
          mimeType: "text/json",
        };
        cy.get("[data-testid='stFileUploadDropzone']").attachFile(file, {
          force: true,
          subjectType: "drag-n-drop",
          events: ["dragenter", "drop"],
        });
      });
      cy.enter('[title="components.tabs.tabs_component"]').then((getBody) => {
        getBody().contains("Metadata").click();
      });
      cy.get("[data-testid='element-container']")
        .contains("Titanic")
        .should("exist");
    });
    it("should download as json", () => {
      cy.visit("http://localhost:8501");
      cy.fixture(fixture).then((fileContent) => {
        const file = {
          fileContent,
          fileName: fixture,
          mimeType: "text/json",
        };
        cy.get("[data-testid='stFileUploadDropzone']").attachFile(file, {
          force: true,
          subjectType: "drag-n-drop",
          events: ["dragenter", "drop"],
        });
      });
      cy.get('[data-testid="stException"]').should("not.exist");
      cy.enter('[title="components.tabs.tabs_component"]').then((getBody) => {
        getBody().contains("Export").click();
      });
      cy.fixture(fixture).then((fileContent) => {
        const downloadsFolder = Cypress.config("downloadsFolder");
        cy.readFile(path.join(downloadsFolder, "croissant-titanic.json"))
          .then((downloadedFile) => {
            downloadedFile = JSON.stringify(downloadedFile);
            return downloadedFile;
          })
          .should("deep.equal", JSON.stringify(fileContent));
      });
    });
  });
});
