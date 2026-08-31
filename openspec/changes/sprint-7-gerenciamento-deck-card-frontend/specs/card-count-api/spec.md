## ADDED Requirements

### Requirement: Card count endpoint returns a minimal response
The system SHALL expose `GET /api/v1/cards/count/?deck_id=<uuid>` and return only an integer `count` field, calculated directly in MongoDB without materializing Card entities.

#### Scenario: Active cards are counted
- **WHEN** an authenticated authorized user requests the count for a deck containing active cards
- **THEN** the response is `200` with exactly `{ "count": N }`

#### Scenario: Soft-deleted cards are excluded
- **WHEN** a deck contains soft-deleted cards
- **THEN** those cards are not included in `count`

#### Scenario: Another user's cards are not exposed
- **WHEN** a user requests the count with another user's deck identifier
- **THEN** the response count is zero

#### Scenario: Deck identifier is required and valid
- **WHEN** `deck_id` is missing or is not a UUID
- **THEN** the endpoint returns `400` without querying or returning card content

### Requirement: Card API uses English content field identifiers
The Card API SHALL accept and return `front`, `back`, `front_description`, and `back_description`; legacy and intermediate Portuguese content field names SHALL no longer be accepted.

#### Scenario: New field names round-trip
- **WHEN** a user creates or updates a card with the four new field names
- **THEN** the API persists and returns those same names and values

#### Scenario: Old and intermediate field names are rejected
- **WHEN** a user attempts to create a card using only `word`/`translation` or `frente`/`verso`
- **THEN** validation fails with `400`
