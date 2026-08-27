## ADDED Requirements

### Requirement: Users can view the cards within a deck
The system SHALL display the list of cards belonging to a deck on that deck's detail view, including an empty state when the deck has no cards.

#### Scenario: Cards are listed within a deck
- **WHEN** an authenticated user opens a deck's detail view
- **THEN** the page shows each card belonging to that deck

#### Scenario: Empty state is shown for a deck with no cards
- **WHEN** an authenticated user opens the detail view of a deck with no cards
- **THEN** the page shows a message indicating there are no cards yet, instead of an empty list

### Requirement: Users can create a card within a deck
The system SHALL provide a form, from the deck's detail view, to create a card with word, translation, example, and tags, associated with that deck.

#### Scenario: Card is created successfully
- **WHEN** an authenticated user submits the card creation form with valid word, translation, and example values
- **THEN** the card is created, associated with the current deck, and appears in the deck's card list

### Requirement: Users can edit a card
The system SHALL provide a form to edit an existing card's word, translation, example, and tags.

#### Scenario: Card is edited successfully
- **WHEN** an authenticated user submits changes to a card they own
- **THEN** the card's updated fields are persisted and reflected in the UI

### Requirement: Users can delete a card with a retention-window warning
The system SHALL require explicit confirmation before deleting a card, and the confirmation SHALL state that the card enters a retention window before permanent removal.

#### Scenario: Card deletion requires confirmation
- **WHEN** an authenticated user initiates deleting a card
- **THEN** a confirmation dialog appears mentioning the retention window before the deletion request is sent

#### Scenario: Confirmed deletion removes the card from the deck's list
- **WHEN** an authenticated user confirms deletion of a card they own
- **THEN** the card no longer appears in the deck's card list
