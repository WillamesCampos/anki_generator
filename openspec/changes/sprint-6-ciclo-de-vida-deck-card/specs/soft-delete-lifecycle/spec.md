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
The system SHALL run a daily scheduled task that permanently deletes `Deck`/`Card`/`Category` records whose `deleted_at` is more than 7 days in the past.

#### Scenario: Purge removes old soft-deleted records
- **WHEN** the daily purge task runs
- **THEN** every `Deck`/`Card`/`Category` with `deleted_at` older than 7 days is physically removed from the database

#### Scenario: Purge preserves records within the retention window
- **WHEN** the daily purge task runs
- **THEN** `Deck`/`Card`/`Category` records with `deleted_at` less than 7 days old are left untouched

### Requirement: Deleting a category marks it for deletion and does not cascade to its decks
The system SHALL, on `DELETE` of a `Category`, set `deleted_at` to the current timestamp instead of physically removing the record, and SHALL NOT cascade the deletion to any `Deck` that references it.

#### Scenario: Deleting a category soft-deletes it
- **WHEN** an authenticated user deletes a category they own
- **THEN** the category's `deleted_at` is set, and the category no longer appears in normal reads

#### Scenario: Category deletion does not delete linked decks
- **WHEN** an authenticated user deletes a category that decks reference via `category_id`
- **THEN** those decks are not deleted and remain accessible

### Requirement: Deleting a category unlinks decks that reference it
The system SHALL set `category_id` to `null` on every `Deck` that references a `Category` being deleted, since `category_id` is an optional organizational label, not an ownership relationship.

#### Scenario: Deck is unlinked when its category is deleted
- **WHEN** a category referenced by a deck's `category_id` is deleted
- **THEN** that deck's `category_id` is set to `null`, and the deck itself is unaffected otherwise
