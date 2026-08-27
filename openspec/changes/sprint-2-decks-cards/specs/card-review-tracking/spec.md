## ADDED Requirements

### Requirement: CardReview is a distinct entity from GenerationSession
The system SHALL introduce a `CardReview` entity representing a single review event for a card (timestamp, rating, resulting schedule change) — distinct from `GenerationSession`, which SHALL continue to represent an AI card-generation job and SHALL NOT be renamed, reused, or repurposed to also represent study review events.

#### Scenario: GenerationSession is untouched
- **WHEN** the `GenerationSession` entity is inspected after this change
- **THEN** its fields and purpose (AI generation job status) are unchanged

#### Scenario: CardReview exists as its own entity
- **WHEN** the domain entities are inspected
- **THEN** `CardReview` exists as a separate entity from `GenerationSession`, with no shared fields implying the two represent the same concept

### Requirement: One CardReview record per review event
The system SHALL persist one `CardReview` document per individual card review — not an aggregated "study session" record — mirroring the granularity Anki itself uses for its review log.

#### Scenario: Reviewing three cards creates three records
- **WHEN** a user reviews three different cards in a row
- **THEN** three separate `CardReview` documents are persisted, each referencing its own card and owner

### Requirement: CardReview is scoped by owner
Every `CardReview` SHALL carry `owner_id` and be subject to the same tenant-isolation guarantees as `Deck`/`Category`/`Card` (see `deck-card-multi-tenant-isolation`).

#### Scenario: Cross-tenant review access is blocked
- **WHEN** a user attempts to read another user's `CardReview` records by ID
- **THEN** the repository returns no result
