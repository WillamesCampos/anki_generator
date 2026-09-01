## ADDED Requirements

### Requirement: Authenticated users can fetch statistics for a specific deck they own
The system SHALL expose `GET /api/v1/decks/{deck_id}/statistics/`, returning, for the authenticated user's own deck: the distribution of `CardReview` records by rating (again/hard/good/easy) and the count of `CardReview` records reviewed today. Both SHALL be computed via a MongoDB aggregation (`$match`/`$facet`/`$group`), scoped by `owner_id` and `deck_id`, never returning raw documents to be summed client-side.

The response SHALL expose `rating_distribution` with all four keys (`again`, `hard`, `good`, `easy`), `reviewed_today`, `daily_review_goal`, and `goal_progress_percentage`. Rating counts SHALL cover the complete active history of the deck; a missing daily goal SHALL produce a null progress percentage.

#### Scenario: User fetches statistics for their own deck
- **WHEN** an authenticated user calls `GET /api/v1/decks/{deck_id}/statistics/` for a deck they own
- **THEN** the response contains the rating distribution and today's reviewed count, scoped to that deck only

#### Scenario: Cross-tenant deck statistics are never returned
- **WHEN** an authenticated user calls `GET /api/v1/decks/{deck_id}/statistics/` for a `deck_id` that exists but belongs to another user
- **THEN** the system returns `404`, never the other user's statistics and never a distinguishable "deck exists but isn't yours" error

#### Scenario: Statistics for a deck with no reviews
- **WHEN** an authenticated user calls `GET /api/v1/decks/{deck_id}/statistics/` for a deck they own that has no `CardReview` records yet
- **THEN** the response contains a zeroed/empty distribution and a "reviewed today" count of 0, not an error
