## ADDED Requirements

### Requirement: Users can view a list of their decks
The system SHALL display a list of the authenticated user's decks at `/decks`, replacing the placeholder page, including an empty state when the user has no decks.

#### Scenario: Decks are listed
- **WHEN** an authenticated user with existing decks navigates to `/decks`
- **THEN** the page shows each deck's title and description

#### Scenario: Empty state is shown
- **WHEN** an authenticated user with no decks navigates to `/decks`
- **THEN** the page shows a message indicating there are no decks yet, instead of an empty list

### Requirement: Users can create a deck
The system SHALL provide a form to create a deck with title, description, category, and daily review goal, submitting to the deck creation endpoint.

#### Scenario: Deck is created successfully
- **WHEN** an authenticated user submits the deck creation form with a valid title
- **THEN** the deck is created and the user is taken to the deck list or the new deck's detail view

### Requirement: Users can edit a deck
The system SHALL provide a form, accessible from the deck's detail view, to edit an existing deck's title, description, category, and daily review goal.

#### Scenario: Deck is edited successfully
- **WHEN** an authenticated user submits changes to a deck they own
- **THEN** the deck's updated fields are persisted and reflected in the UI

### Requirement: Users can delete a deck with a retention-window warning
The system SHALL require explicit confirmation before deleting a deck, and the confirmation SHALL state that the deck enters a retention window before permanent removal.

#### Scenario: Deck deletion requires confirmation
- **WHEN** an authenticated user initiates deleting a deck
- **THEN** a confirmation dialog appears mentioning the retention window before the deletion request is sent

#### Scenario: Confirmed deletion removes the deck from the list
- **WHEN** an authenticated user confirms deletion of a deck they own
- **THEN** the deck no longer appears in the deck list
