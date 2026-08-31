## ADDED Requirements

### Requirement: Deck detail shows its historical rating distribution
The system SHALL show a Chart.js bar chart on `/decks/:deckId` using `rating_distribution` from `GET /api/v1/decks/{deck_id}/statistics/`, with the labels `Errou`, `Difícil`, `Bom`, and `Fácil` in that order.

#### Scenario: Deck has review history
- **WHEN** an authenticated owner opens a deck whose cards have historical reviews
- **THEN** the chart shows the all-time counts for `again`, `hard`, `good`, and `easy` belonging to that deck only

#### Scenario: Deck has no review history
- **WHEN** an authenticated owner opens a deck without reviews
- **THEN** the chart renders the four classifications with zero values instead of an empty or error state

#### Scenario: Statistics request fails
- **WHEN** the dedicated statistics endpoint fails
- **THEN** the card count and deck actions remain usable and the statistics section shows its own error message

### Requirement: Home and deck detail use the same deck-scoped distribution
When the Home identifies the most recently studied deck from the newest `CardReview`, the system SHALL fetch that deck's `rating_distribution` from `GET /api/v1/decks/{deck_id}/statistics/`. The Home SHALL NOT derive the chart by summing the paginated `GET /api/v1/reviews/` response across decks.

#### Scenario: The most recently studied deck is shown on Home and detail
- **WHEN** the newest review belongs to a deck whose historical rating distribution is available
- **THEN** the Home chart and that deck's detail chart show the same `again`, `hard`, `good`, and `easy` counts

#### Scenario: Reviews from other decks are present in the recent page
- **WHEN** `GET /api/v1/reviews/` contains recent reviews from multiple decks
- **THEN** those other decks influence which review is newest but do not contribute to the Home chart
