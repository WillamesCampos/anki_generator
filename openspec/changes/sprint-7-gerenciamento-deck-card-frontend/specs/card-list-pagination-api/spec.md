## ADDED Requirements

### Requirement: Card lists use a dedicated ten-item page size
The system SHALL paginate `GET /api/v1/cards/?deck_id=<uuid>&page=<number>` with exactly 10 cards per page and the standard DRF `count`, `next`, `previous`, and `results` response fields, without changing pagination for other resources.

#### Scenario: Deck has more than ten active cards
- **WHEN** an authorized owner requests page 1 for a deck with 11 active cards
- **THEN** the response contains `count: 11`, exactly 10 `results`, a non-null `next`, and a null `previous`

#### Scenario: Owner requests the final page
- **WHEN** the authorized owner requests page 2 for that deck
- **THEN** the response contains the remaining card, a null `next`, and a non-null `previous`

#### Scenario: Pagination preserves tenant isolation and soft deletion
- **WHEN** a page is requested for a deck containing another owner's cards or soft-deleted cards
- **THEN** neither those cards nor their quantities contribute to `count` or `results`
