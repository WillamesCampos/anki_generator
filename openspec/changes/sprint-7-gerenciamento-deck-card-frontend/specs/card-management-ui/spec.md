## ADDED Requirements

### Requirement: Users can view a card count on the deck detail
The system SHALL display only the number of active cards belonging to a deck on that deck's detail view, without downloading the card list.

#### Scenario: Card count is shown on deck detail
- **WHEN** an authenticated user opens a deck's detail view
- **THEN** the page requests the dedicated count endpoint and shows the singular or plural card count

### Requirement: Users navigate to a dedicated card list
The system SHALL provide a "Ver todos os cards" button on the deck detail that navigates to `/decks/:deckId/cards`, where the complete card list and management actions are rendered.

#### Scenario: User opens all cards
- **WHEN** an authenticated user activates "Ver todos os cards"
- **THEN** the dedicated card page for the current deck opens

#### Scenario: Empty state is shown on the dedicated page
- **WHEN** an authenticated user opens the dedicated page for a deck with no cards
- **THEN** the page shows a message indicating there are no cards yet, instead of an empty list

### Requirement: Users can create a card within a deck
The system SHALL provide a form on the dedicated card page to create a card with internal fields `front`, `back`, `front_description`, `back_description`, and tags, associated with that deck. Its visible labels SHALL remain in Portuguese.

#### Scenario: Creation form precedes the card list
- **WHEN** an authenticated user opens the dedicated card page
- **THEN** the creation form is rendered before the paginated card list in document order

#### Scenario: Card is created successfully
- **WHEN** an authenticated user submits the card creation form with valid content values
- **THEN** the card is created, associated with the current deck, and appears in the dedicated card list

### Requirement: Users can edit a card
The system SHALL provide a form to edit an existing card's `front`, `back`, `front_description`, `back_description`, and tags while retaining Portuguese labels.

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

### Requirement: Users navigate cards ten at a time
The system SHALL display the deck's cards in pages of 10 and SHALL provide previous/next controls plus the current and total page numbers.

#### Scenario: First page has more results available
- **WHEN** a deck contains more than 10 active cards and the user opens its dedicated card page
- **THEN** only the first 10 cards are rendered and the next-page control is enabled

#### Scenario: User opens another page
- **WHEN** the user activates the next-page control
- **THEN** the page requests and renders the next 10 cards without duplicating cards from the previous page

#### Scenario: Pagination remains valid after deletion
- **WHEN** the user deletes the only card on a page after the first
- **THEN** the preceding valid page is loaded instead of leaving the user on an empty out-of-range page
