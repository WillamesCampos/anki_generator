## ADDED Requirements

### Requirement: Owners can edit their deck's name, category, and goal
The system SHALL allow the owner of a `Deck` to update its `title`, `category_id`, and `daily_review_goal` via `PATCH`.

#### Scenario: Owner edits deck name and category
- **WHEN** an authenticated user PATCHes their deck with a new `title` and `category_id`
- **THEN** the deck reflects both changes on subsequent reads

### Requirement: Owners can edit their card's content and tags
The system SHALL allow the owner of a `Card` to update its content fields (word/translation/example) and `tags` via `PATCH`.

#### Scenario: Owner edits card tags
- **WHEN** an authenticated user PATCHes their card with a new set of `tags`
- **THEN** the card reflects the updated tags on subsequent reads

### Requirement: Editing a deck or card never accepts owner_id, created_by, or updated_by as input
The system SHALL ignore `owner_id`, `created_by`, and `updated_by` when present in a `PATCH` payload for `Deck` or `Card`, consistent with existing multi-tenant and audit-trail protections.

#### Scenario: Client attempts to change ownership via PATCH
- **WHEN** an authenticated user PATCHes their deck with a different `owner_id` in the payload
- **THEN** the deck's `owner_id` remains unchanged
