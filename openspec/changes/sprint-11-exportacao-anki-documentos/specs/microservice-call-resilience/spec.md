## ADDED Requirements

### Requirement: Transient failures calling document-generator are retried with exponential backoff
The system SHALL retry a failed call to the `document-generator` microservice (timeout, connection error, or 5xx response) using exponential backoff, up to a bounded number of attempts, before treating the operation as failed.

#### Scenario: Call succeeds after a transient failure
- **WHEN** a call to `document-generator` fails once (e.g. a transient timeout) and succeeds on a subsequent attempt within the retry limit
- **THEN** the caller receives the successful result, with no failure surfaced to the Celery task

#### Scenario: Call fails after exhausting retries
- **WHEN** a call to `document-generator` fails on every attempt up to the configured retry limit
- **THEN** the operation is reported as failed exactly once to the circuit breaker, not once per retry attempt

#### Scenario: Client errors are neither retried nor counted
- **WHEN** a call to `document-generator` returns a 4xx response (e.g. `400` for an invalid request or `401` for an invalid service token)
- **THEN** the operation fails immediately without retry, and the failure is not counted by the circuit breaker

### Requirement: Circuit breaker short-circuits calls after repeated failures
The system SHALL wrap the entire retrying operation (not each individual retry attempt) in a circuit breaker. After a configured number of consecutive failed operations, the breaker SHALL open and reject subsequent calls immediately, without attempting any network request, until a cooldown period elapses.

#### Scenario: Breaker opens after consecutive failures
- **WHEN** the retrying operation against `document-generator` fails consecutively past the configured threshold
- **THEN** the breaker transitions to open, and further calls fail immediately without hitting the network

#### Scenario: Breaker tests recovery after cooldown
- **WHEN** the cooldown period elapses while the breaker is open
- **THEN** the breaker allows exactly one call through (half-open); if it succeeds the breaker closes, if it fails the breaker reopens and the cooldown restarts

#### Scenario: Breaker stays closed under normal operation
- **WHEN** calls to `document-generator` succeed within their retry budget
- **THEN** the breaker remains closed and never short-circuits a call

### Requirement: Circuit breaker state is shared across worker processes
The circuit breaker's failure counter and state SHALL be stored in a shared store (Redis), scoped per target service, so that all worker processes observe the same state.

#### Scenario: Failures in one process open the breaker for all
- **WHEN** failed operations counted by one worker process reach the failure threshold
- **THEN** calls made from any other worker process to the same service are short-circuited as well

### Requirement: Resilience policy is set per call site
Timeout and retry attempts SHALL be configurable per call site while the breaker of a target service is shared. A long-running call (deck export) SHALL use its own, larger timeout than short calls to the same service.

#### Scenario: Export uses its own timeout
- **WHEN** the deck export calls `document-generator`
- **THEN** it uses the export-specific timeout, not the default one used by other calls

### Requirement: Resilience wrapper is reusable across microservice calls
The circuit breaker and retry combination SHALL be implemented as a reusable wrapper around outgoing service-to-service HTTP calls, not hardcoded to the `document-generator` export call specifically, so future microservice integrations (Sprint 13, Sprint 14) can adopt the same mechanism.

#### Scenario: A second microservice call reuses the same resilience wrapper
- **WHEN** a future call to a different microservice is implemented using the resilience wrapper
- **THEN** it gets retry and circuit breaker behavior without reimplementing the failure-counting or backoff logic
