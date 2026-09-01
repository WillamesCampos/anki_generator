## ADDED Requirements

### Requirement: CI runs on every pull request targeting main
The system SHALL run the lint, backend-test, and frontend-test jobs automatically whenever a pull request is opened or updated against `main`.

#### Scenario: PR opened against main
- **WHEN** a pull request is opened or pushed to, targeting `main`
- **THEN** the `lint`, `backend-test`, and `frontend-test` jobs run and report status checks on that PR

### Requirement: CI runs again on merge to main
The system SHALL run the same lint, backend-test, and frontend-test jobs whenever a commit lands on `main` (via merge or direct push), independently of whether those jobs already ran on the originating pull request.

#### Scenario: PR merged into main
- **WHEN** a pull request is merged into `main`
- **THEN** the `lint`, `backend-test`, and `frontend-test` jobs run again against the resulting `main` commit

### Requirement: Lint, backend tests, and frontend tests run as independent jobs
The system SHALL run linting, backend tests, and frontend tests as three separate CI jobs that can succeed or fail independently, rather than as a single combined step.

#### Scenario: Only frontend lint fails
- **WHEN** the frontend has a lint violation but the backend lint, backend tests, and frontend tests all pass
- **THEN** only the `lint` job is reported as failed, while `backend-test` and `frontend-test` are reported as passed

### Requirement: Backend tests run against real service dependencies
The system SHALL run backend tests (`pytest`) against Postgres, MongoDB, and Redis service containers provisioned by the CI job, not against mocks of those services.

#### Scenario: Backend test job provisions its dependencies
- **WHEN** the `backend-test` job runs
- **THEN** Postgres, MongoDB, and Redis are available to the test run as service containers, and `pytest apps/` runs against them
