## ADDED Requirements

### Requirement: Google OAuth login via maintained libraries
The system SHALL implement Google OAuth login using `django-allauth` (OAuth handshake) and `dj-rest-auth` (REST endpoints for the SPA), rather than a hand-rolled OAuth2 flow.

#### Scenario: Successful Google login issues a JWT
- **WHEN** a user completes the Google OAuth flow successfully
- **THEN** the system returns a JWT access token and refresh token (via `simplejwt`), not a server-rendered page or session cookie

#### Scenario: No manual OAuth2 implementation exists
- **WHEN** the codebase is inspected for OAuth2 handshake logic (state validation, token exchange with Google)
- **THEN** this logic lives entirely inside `django-allauth`/`dj-rest-auth`, not in project-specific code

### Requirement: JWT-based authentication with revocable refresh tokens
The system SHALL issue short-lived JWT access tokens (10–15 minutes) and longer-lived refresh tokens, with refresh token state tracked in Redis to allow revocation (logout, compromise) before natural expiration.

#### Scenario: Expired access token is rejected
- **WHEN** a request is made with an access token past its expiration
- **THEN** the request is rejected with an authentication error, independent of the refresh token's validity

#### Scenario: Logout revokes the refresh token
- **WHEN** a user logs out
- **THEN** their refresh token is invalidated in Redis and can no longer be used to obtain a new access token

#### Scenario: No cookie-based session is used for the API
- **WHEN** the SPA authenticates against the Django API
- **THEN** it does so via JWT in an `Authorization` header, not via a session cookie
