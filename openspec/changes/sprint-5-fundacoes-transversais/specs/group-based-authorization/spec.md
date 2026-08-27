## ADDED Requirements

### Requirement: Every user is assigned to the standard_user group automatically
The system SHALL add every user to the Django `Group` named `standard_user` automatically upon account creation (signup via Google, signup via email/password, and the seed command) — no manual assignment step required.

#### Scenario: New signup gets the standard_user group
- **WHEN** a new user account is created through any signup path
- **THEN** that user is a member of the `standard_user` group without further action

### Requirement: Deck/card/category/review endpoints require group membership, not just authentication
The system SHALL require membership in an authorized group (at minimum `standard_user`) to access `decks`/`cards`/`categories`/`reviews` endpoints, replacing the plain `IsAuthenticated` check used until this change.

#### Scenario: Authenticated user in standard_user group can access endpoints
- **WHEN** an authenticated user who belongs to `standard_user` calls a decks/cards endpoint
- **THEN** the request is authorized normally, subject to existing ownership (`owner_id`) filtering

#### Scenario: Authenticated user without any authorized group is denied
- **WHEN** an authenticated user who belongs to no authorized group calls a decks/cards endpoint
- **THEN** the system denies the request, distinct from an unauthenticated (401) request
