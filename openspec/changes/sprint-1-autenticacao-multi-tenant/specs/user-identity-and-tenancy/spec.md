## ADDED Requirements

### Requirement: Custom user model with unique email
The system SHALL provide a custom Django user model extending the native `AbstractUser`, adding `email` as a unique field usable as an alternate authentication key, defined before any other real migration is applied.

#### Scenario: Duplicate email rejected
- **WHEN** a second user is created with an email already in use by another user
- **THEN** the system rejects the creation with a validation error

#### Scenario: User created via native Django tooling
- **WHEN** an administrator creates a user via `createsuperuser` or the Django admin
- **THEN** the resulting user is an instance of the custom user model, with `email` required and unique

### Requirement: Tenant isolation is per-user, not per-organization
The system SHALL treat "tenant" as equivalent to "user" — every user-owned record SHALL carry a direct foreign key to the owning user, with no intermediate `Tenant`/`Organization` model.

#### Scenario: No Organization model exists
- **WHEN** the codebase is inspected for a `Tenant` or `Organization` model
- **THEN** none exists; ownership is expressed via a direct FK to the user model on each owned record

### Requirement: Reusable tenant-scoped queryset mixin
The system SHALL provide a reusable queryset/manager mixin that filters any user-owned model's queryset to only the records owned by the requesting user, so that every model needing tenant isolation applies the same mechanism instead of duplicating filter logic per view.

#### Scenario: Cross-tenant access attempt is blocked
- **WHEN** a user attempts to read, update, or delete a record owned by a different user, by ID, through any endpoint using the mixin
- **THEN** the system behaves as if the record does not exist for that user (404, not a 403 that would confirm existence)

#### Scenario: Mixin is reused, not reimplemented, by future models
- **WHEN** a new user-owned Django model is added in a future sprint (e.g., Sprint 2 decks/cards models)
- **THEN** it applies tenant isolation by using the shared mixin, not by writing a new ad-hoc filter
