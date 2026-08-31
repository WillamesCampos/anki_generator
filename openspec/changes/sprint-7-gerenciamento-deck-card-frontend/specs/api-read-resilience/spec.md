## ADDED Requirements

### Requirement: API permits ten requests per second
The system SHALL enforce global authenticated and anonymous throttle rates of 10 requests per second using the configured shared cache.

#### Scenario: Requests within the limit succeed
- **WHEN** a client sends ten otherwise-valid requests inside one throttle window
- **THEN** all ten requests are processed normally

#### Scenario: Request over the limit is throttled
- **WHEN** the same client sends an eleventh request inside that window
- **THEN** the API returns `429 Too Many Requests`

### Requirement: Concurrent deck reads do not invalidate MongoDB connectivity
The system SHALL execute Motor repository coroutines from synchronous Django entry points on a persistent process-local event loop.

#### Scenario: Detail and count are requested concurrently
- **WHEN** authenticated requests for a deck detail and its card count execute concurrently
- **THEN** both complete with `200` and neither raises a MongoDB connection or event-loop error
