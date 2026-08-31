## ADDED Requirements

### Requirement: pytest + pytest-django configured as the project's test runner
The system SHALL have `pytest` and `pytest-django` configured for the Django project (`django/`), as the first automated testing infrastructure introduced in the project (Sprint 0 intentionally had none).

#### Scenario: Test suite runs via a single command
- **WHEN** a developer runs the project's test command (e.g., `poetry -C django run pytest`)
- **THEN** the full automated test suite for the Django project executes and reports pass/fail

### Requirement: Automated tests written after feature tasks, covering this sprint's critical behaviors
The system SHALL have automated tests covering, at minimum, tenant isolation (cross-tenant access is blocked) and rate limiting (requests over 3/s are rejected), written after the corresponding feature tasks are implemented — not test-first.

#### Scenario: Multi-tenant isolation test exists and passes
- **WHEN** the test suite runs
- **THEN** a test simulating a cross-tenant access attempt asserts the access is blocked

#### Scenario: Rate limiting test exists and passes
- **WHEN** the test suite runs
- **THEN** a test simulating requests above 10 req/s asserts a `429` response is returned
