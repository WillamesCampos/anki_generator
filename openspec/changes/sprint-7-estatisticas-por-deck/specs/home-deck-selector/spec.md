## ADDED Requirements

### Requirement: Home dashboard offers a deck selector above the statistics chart
The system SHALL render a dropdown above the Home statistics chart, listing the authenticated user's decks (`GET /api/v1/decks/`). Selecting a deck SHALL fetch and display that deck's statistics (`deck-statistics-api`), replacing whatever was shown before.

#### Scenario: User selects a deck from the dropdown
- **WHEN** an authenticated user selects a deck in the Home dropdown
- **THEN** the statistics chart updates to reflect only that deck's data

### Requirement: Without manual selection, the Home defaults to the most recently studied deck
The system SHALL, when no deck has been manually selected in the dropdown, display statistics for the most recently studied deck — the same deck already resolved today via the user's most recent `CardReview`.

#### Scenario: First load with study history
- **WHEN** an authenticated user with prior reviews loads the Home page without touching the dropdown
- **THEN** the deck card and statistics chart show the most recently studied deck's data

### Requirement: Card title reflects whether the shown deck is automatic or manually selected
The system SHALL label the deck info card "Último deck estudado" when showing the automatic default (most recently studied), and SHALL relabel it "Deck estudado" once the user manually selects a deck from the dropdown.

#### Scenario: Title changes on manual selection
- **WHEN** an authenticated user manually selects a deck in the dropdown
- **THEN** the deck info card's title changes from "Último deck estudado" to "Deck estudado"

#### Scenario: Title stays default without interaction
- **WHEN** an authenticated user has not interacted with the dropdown
- **THEN** the deck info card's title remains "Último deck estudado"
