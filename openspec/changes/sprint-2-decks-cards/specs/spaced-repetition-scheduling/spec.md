## ADDED Requirements

### Requirement: Card carries FSRS scheduling fields
The `Card` entity SHALL carry the fields required by the FSRS (Free Spaced Repetition Scheduler) algorithm — at minimum `stability`, `difficulty`, `due_at`, and `state` — persisted in MongoDB.

#### Scenario: New card has default scheduling state
- **WHEN** a `Card` is created for the first time
- **THEN** it has FSRS default scheduling values (never-reviewed state) and a `due_at` allowing it to be studied immediately

### Requirement: Scheduling computed via the fsrs package
The system SHALL compute the next review interval and updated scheduling fields using the `fsrs` Python package, not a hand-rolled implementation of SM-2 or any other algorithm.

#### Scenario: Reviewing a card updates its schedule via fsrs
- **WHEN** a card review is registered with a given rating
- **THEN** the system calls the `fsrs` package to compute the new `stability`/`difficulty`/`due_at`, and persists the updated `Card`

### Requirement: Due cards are queryable per user
The system SHALL support querying, per owner, which cards are due for review at a given point in time (`due_at <= now`), to support the future study flow.

#### Scenario: Only due cards are returned
- **WHEN** a repository query for "due cards" is executed for a given user at a given time
- **THEN** only cards owned by that user with `due_at` at or before that time are returned
