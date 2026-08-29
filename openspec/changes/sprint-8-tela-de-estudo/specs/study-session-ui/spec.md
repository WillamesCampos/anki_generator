## ADDED Requirements

### Requirement: Users can start a study session from a deck
The system SHALL provide a way to start a study session from a deck's detail view, showing only that deck's due cards.

#### Scenario: Starting a study session
- **WHEN** an authenticated user clicks "Estudar" on a deck they own
- **THEN** the system navigates to a study session showing that deck's due cards

### Requirement: A study session fetches due cards once and does not persist session state
The system SHALL fetch the deck's due cards once when the study session starts, and SHALL NOT persist any session state (such as current position) across page reloads or app restarts.

#### Scenario: Reopening the study session starts fresh
- **WHEN** an authenticated user leaves a study session before finishing and starts a new one for the same deck
- **THEN** the new session fetches the currently due cards again, with no memory of the prior session's position

### Requirement: A study session shows a card's front, then reveals its back on demand
The system SHALL show a card's term first, and reveal its translation and example only after the user requests it.

#### Scenario: Revealing the back of a card
- **WHEN** an authenticated user requests to see the answer for the current card
- **THEN** the translation and example become visible

### Requirement: Rating a card submits a review and advances to the next card
The system SHALL submit the selected rating (`again`, `hard`, `good`, or `easy`) for the current card, then advance to the next card in the session's list without re-querying due cards.

#### Scenario: Rating advances the session
- **WHEN** an authenticated user rates the currently shown card
- **THEN** a review is submitted for that card and the next card in the session's list is shown

#### Scenario: Rating the last card ends the session
- **WHEN** an authenticated user rates the last card in the session's list
- **THEN** the system shows a session-complete state instead of another card

### Requirement: A study session shows progress and an empty state
The system SHALL show the user's progress through the session (current position out of total), and SHALL show a distinct message when a deck has no due cards instead of an empty session.

#### Scenario: Progress is shown during a session
- **WHEN** an authenticated user is partway through a study session
- **THEN** the UI shows how many cards have been reviewed out of the session's total

#### Scenario: Empty state for a deck with no due cards
- **WHEN** an authenticated user starts a study session for a deck with no due cards
- **THEN** the system shows a message indicating there is nothing due, instead of an empty session
