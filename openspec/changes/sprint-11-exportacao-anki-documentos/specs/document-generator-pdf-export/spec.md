## ADDED Requirements

### Requirement: document-generator exposes generic PDF generation, protected like the existing export route
The system SHALL expose `POST /document-generator/v1/documents/pdf` on the `document-generator` microservice, accepting a generic document payload (title and content sections) and returning a generated PDF file. The route SHALL be protected by the same `require_service_jwt` dependency already used by `/decks/export`, with no separate authentication mechanism.

#### Scenario: Authenticated service generates a PDF
- **WHEN** a caller with a valid service JWT sends a title and content sections to `POST /document-generator/v1/documents/pdf`
- **THEN** the system returns a generated PDF file matching the submitted content

#### Scenario: Request without a valid service JWT is rejected
- **WHEN** a caller sends a request to `POST /document-generator/v1/documents/pdf` without a valid service JWT
- **THEN** the system responds `401` and does not generate a document

### Requirement: PDF generation has no Django consumer in this sprint
The system SHALL expose the PDF generation capability as a standalone, reusable building block. No Django endpoint or Celery task SHALL call it yet — it is consumed starting in Sprint 15 (weekly email report).

#### Scenario: PDF route exists without being invoked by any Django flow
- **WHEN** Sprint 11 is complete
- **THEN** `POST /document-generator/v1/documents/pdf` is reachable and tested in isolation, with no Django code path calling it
