## ADDED Requirements

### Requirement: Backend Python code is checked for formatting via black
The system SHALL provide a `black` configuration for the Django project and a way to check formatting compliance without modifying files (`black --check`).

#### Scenario: Unformatted code fails the check
- **WHEN** a Python file under `django/` does not conform to `black`'s formatting
- **THEN** `black --check .` exits with a non-zero status, identifying the non-conformant file

#### Scenario: Formatted code passes the check
- **WHEN** every Python file under `django/` conforms to `black`'s formatting
- **THEN** `black --check .` exits with a zero status

### Requirement: Local pre-commit hook enforces formatting before commit
The system SHALL provide a `.pre-commit-config.yaml` with the official `black` hook, so contributors can enforce formatting locally before code reaches CI.

#### Scenario: Contributor installs the pre-commit hook
- **WHEN** a contributor runs `pre-commit install` in the repository
- **THEN** subsequent commits touching Python files under `django/` are automatically checked/reformatted by `black` before the commit completes
