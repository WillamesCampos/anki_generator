## ADDED Requirements

### Requirement: A deck can have a daily review goal set by its owner
The system SHALL allow the owner of a `Deck` to set and edit `daily_review_goal`, an optional integer representing how many cards from that deck they intend to review.

#### Scenario: Owner sets a review goal
- **WHEN** an authenticated user PATCHes their deck with a `daily_review_goal` value
- **THEN** the deck's `daily_review_goal` is updated to that value, persisted server-side

#### Scenario: Deck without a goal has no goal
- **WHEN** a deck has never had `daily_review_goal` set
- **THEN** the field is absent/null, not defaulted to an arbitrary number
