## ADDED Requirements

### Requirement: Deleting a deck or card marks it for deletion instead of removing it immediately
The system SHALL, on `DELETE` of a `Deck` or `Card`, set `deleted_at` to the current timestamp instead of physically removing the record.

#### Scenario: Deleting a deck soft-deletes it
- **WHEN** an authenticated user deletes a deck they own
- **THEN** the deck's `deleted_at` is set, and the deck no longer appears in normal reads

### Requirement: Deleting a deck cascades to all its cards
The system SHALL, on deletion of a `Deck`, also set `deleted_at` on every `Card` belonging to that deck, since a card belongs to exactly one deck.

#### Scenario: Deck deletion soft-deletes its cards
- **WHEN** an authenticated user deletes a deck that has cards
- **THEN** every card belonging to that deck also has `deleted_at` set

### Requirement: Soft-deleted records are excluded from normal reads by default
The system SHALL exclude records with `deleted_at` set from every existing read path (list, detail, FSRS due-cards lookup, statistics aggregation) unless a caller explicitly requests deleted records.

#### Scenario: Soft-deleted deck is excluded from list
- **WHEN** an authenticated user lists their decks after deleting one
- **THEN** the deleted deck does not appear in the list

### Requirement: CardReview is never deleted, soft or physical
The system SHALL never set `deleted_at` on or physically remove a `CardReview`, regardless of whether its associated card or deck has been deleted.

#### Scenario: CardReview survives its card's deletion
- **WHEN** a card with existing `CardReview` records is deleted
- **THEN** those `CardReview` records still exist in the database afterward, unmodified

### Requirement: Records soft-deleted for more than 7 days are permanently purged
The system SHALL run a daily scheduled task that permanently deletes `Deck`/`Card` records whose `deleted_at` is more than 7 days in the past.

#### Scenario: Purge removes old soft-deleted records
- **WHEN** the daily purge task runs
- **THEN** every `Deck`/`Card` with `deleted_at` older than 7 days is physically removed from the database

#### Scenario: Purge preserves records within the retention window
- **WHEN** the daily purge task runs
- **THEN** `Deck`/`Card` records with `deleted_at` less than 7 days old are left untouched
