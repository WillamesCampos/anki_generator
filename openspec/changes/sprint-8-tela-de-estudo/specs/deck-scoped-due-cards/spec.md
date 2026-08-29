## ADDED Requirements

### Requirement: Due cards can be filtered by deck
The system SHALL allow querying due cards scoped to a specific deck, in addition to the existing user-wide due query.

#### Scenario: Due cards filtered by deck
- **WHEN** an authenticated user requests due cards with both `due=true` and `deck_id` set to a deck they own
- **THEN** the response contains only due cards belonging to that deck

#### Scenario: Due cards without a deck filter remain user-wide
- **WHEN** an authenticated user requests due cards with `due=true` and no `deck_id`
- **THEN** the response contains due cards across all of that user's decks, unchanged from prior behavior

### Requirement: Deck-scoped due cards respect multi-tenant isolation
The system SHALL never return due cards belonging to a deck owned by a different user, regardless of the `deck_id` supplied.

#### Scenario: Requesting another user's deck returns no cards
- **WHEN** an authenticated user requests due cards with `deck_id` set to a deck owned by a different user
- **THEN** the response is empty, not an error revealing the deck's existence
