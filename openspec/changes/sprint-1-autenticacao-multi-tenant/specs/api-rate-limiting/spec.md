## ADDED Requirements

### Requirement: Per-user/client rate limiting at 3 requests/second
The system SHALL throttle API requests to 3 requests/second per authenticated user/client, using DRF's built-in throttle classes backed by the Redis cache already configured in Sprint 0.

#### Scenario: Requests within the limit succeed
- **WHEN** a user/client sends requests at or below 3 requests/second
- **THEN** all requests are processed normally

#### Scenario: Requests over the limit are rejected
- **WHEN** a user/client exceeds 3 requests/second
- **THEN** subsequent requests within that window receive a `429 Too Many Requests` response

#### Scenario: No custom throttling implementation
- **WHEN** the codebase is inspected for rate limiting logic
- **THEN** it uses DRF's `DEFAULT_THROTTLE_CLASSES`/`DEFAULT_THROTTLE_RATES` configuration and the existing Redis cache backend, not a bespoke rate-limiting mechanism
