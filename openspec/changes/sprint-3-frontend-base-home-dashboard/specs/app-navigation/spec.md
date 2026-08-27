## ADDED Requirements

### Requirement: Sidebar navigation lists the product's main sections
The system SHALL provide a sidebar menu listing: decks, categories, report generation, and an AI chat entry — using the design tokens (see `design-tokens` capability), not ad-hoc styling.

#### Scenario: All four sections are listed
- **WHEN** the sidebar renders
- **THEN** it shows entries for decks, categories, report generation, and AI chat

### Requirement: AI chat entry is a visual placeholder without backend
The system SHALL render the AI chat sidebar entry as a placeholder — it SHALL NOT call any backend endpoint, since no AI agent exists until Sprint 5.

#### Scenario: Clicking AI chat does not error
- **WHEN** a user clicks the AI chat sidebar entry
- **THEN** the SPA shows a placeholder view (e.g. "coming soon") and makes no API call related to AI chat
