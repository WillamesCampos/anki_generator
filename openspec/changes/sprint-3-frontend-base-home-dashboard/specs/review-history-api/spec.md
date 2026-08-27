## ADDED Requirements

### Requirement: Authenticated users can list their own review history
The system SHALL expose `GET /api/v1/reviews/`, returning the authenticated user's `CardReview` records, most recent first, scoped by `owner_id` like every other decks/cards endpoint (ver `deck-card-multi-tenant-isolation`, Sprint 2).

#### Scenario: User sees only their own reviews
- **WHEN** an authenticated user calls `GET /api/v1/reviews/`
- **THEN** the response contains only `CardReview` records owned by that user, ordered by `reviewed_at` descending

#### Scenario: Cross-tenant review data is never returned
- **WHEN** a user with no reviews of their own calls `GET /api/v1/reviews/`
- **THEN** the response is empty, never another user's review history
