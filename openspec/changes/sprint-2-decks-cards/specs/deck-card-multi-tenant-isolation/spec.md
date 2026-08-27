## ADDED Requirements

### Requirement: Owner field on every Mongo-backed domain record
The system SHALL store a direct `owner_id` field on `Deck`, `Category`, and `Card` documents in MongoDB — not only via a transitive reference (e.g. `Card.deck_id`) — so that any single-collection query can filter by tenant without a join-like lookup.

#### Scenario: Card carries its own owner_id
- **WHEN** a `Card` document is inspected in MongoDB
- **THEN** it has a non-null `owner_id` field, independent of `deck_id`

### Requirement: Repository methods require owner_id, never optional
Every read/write method on `DeckRepository`, `CategoryRepository`, and `CardRepository` SHALL require `owner_id` as a mandatory parameter and SHALL embed it directly in the MongoDB query filter — never fetch a record by ID alone and check ownership afterward in application code.

#### Scenario: Query is scoped at the database level
- **WHEN** `find_by_id(card_id, owner_id)` is called
- **THEN** the MongoDB query filter includes both `_id` and `owner_id` in the same `find_one` call

#### Scenario: Cross-tenant access by ID is blocked
- **WHEN** a user attempts to read, update, or delete a `Deck`, `Category`, or `Card` owned by a different user, by ID, through any repository method
- **THEN** the repository returns no result (as if the record does not exist), regardless of whether the ID itself is valid

### Requirement: Compound indexes support tenant-scoped queries
The system SHALL create compound MongoDB indexes including `owner_id` (e.g. `{owner_id: 1, deck_id: 1}`) on collections queried by tenant, so tenant-scoped queries remain performant as data grows.

#### Scenario: Index exists on card collection
- **WHEN** the `cards` collection indexes are inspected
- **THEN** a compound index including `owner_id` and `deck_id` exists

### Requirement: Automated test for cross-tenant isolation against real MongoDB
The system SHALL include an automated test, run against a real MongoDB instance (not mocked), that verifies a user cannot access another user's deck/category/card by ID.

#### Scenario: Test fails if isolation regresses
- **WHEN** the cross-tenant isolation test suite runs
- **THEN** it creates records for two distinct owners and asserts that owner B cannot retrieve owner A's record via any repository method, and vice versa
