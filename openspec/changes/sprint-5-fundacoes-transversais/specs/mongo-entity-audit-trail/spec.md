## ADDED Requirements

### Requirement: Deck/Card/Category/CardReview record who created and last updated them
The system SHALL populate `created_by` on creation and `updated_by` on every update of `Deck`, `Card`, `Category`, and `CardReview`, using the authenticated request's user — never accepting either field as client input.

#### Scenario: Creating a deck records the creator
- **WHEN** an authenticated user creates a new deck
- **THEN** the stored `Deck` document has `created_by` set to that user, without the client having sent it

#### Scenario: Client-supplied audit fields are ignored
- **WHEN** an authenticated user sends a request with `created_by` or `updated_by` in the payload
- **THEN** the system ignores those values and uses the authenticated user instead

#### Scenario: Updating a deck records the last editor
- **WHEN** an authenticated user updates a deck they own
- **THEN** the stored `Deck` document has `updated_by` set to that user, while `created_by` remains unchanged from creation
