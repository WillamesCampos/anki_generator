## ADDED Requirements

### Requirement: Root-level Docker Compose environment
The system SHALL provide a `docker-compose.yml` at the project root that brings up all services needed for local development: Django, PostgreSQL (Django's own `auth`/`Permission`/`Group`/sessions/admin database — never SQLite, for dev/prod parity), MongoDB (deck/card/statistics persistence), Redis (Celery result backend/cache), RabbitMQ (Celery broker), and any FastAPI microservice already implemented. This replaces the current orphaned Postgres target in the root `Makefile` (which today starts a Postgres container no code actually uses) with a Postgres that is genuinely wired to Django.

#### Scenario: Full stack starts with a single command
- **WHEN** a developer runs the documented compose command (e.g., `make up` or `docker compose up`)
- **THEN** Django, PostgreSQL, MongoDB, Redis, and RabbitMQ containers all start successfully and can reach each other on the compose network

#### Scenario: Postgres is actually used by Django
- **WHEN** Django's database settings are inspected
- **THEN** they point to the PostgreSQL container defined in `docker-compose.yml`, not SQLite and not an orphaned/unused container

### Requirement: Non-root containers with entrypoint scripts
Every container defined in the local dev environment SHALL run as a dedicated non-root user and SHALL start via an `entrypoint` script, per the existing rule in `PROMPT_REFINADO.md`.

#### Scenario: Container user is inspected
- **WHEN** `whoami` is run inside any running application container
- **THEN** it returns a project-specific non-root user, never `root`

### Requirement: Unified dependency management
The system SHALL have a single, consistent source of truth for Python dependencies per service (Poetry for the Django project, `venv`/`requirements.txt` for each FastAPI microservice), with no dessynchronized duplicate dependency files for the same service.

#### Scenario: Dependency files agree
- **WHEN** `pyproject.toml` (or the relevant `requirements.txt`) for a service is inspected
- **THEN** it accurately lists every third-party package actually imported by that service's code, with no stale or missing entries

### Requirement: Environment variables loaded via python-dotenv
Each service SHALL load configuration from a `.env` file via `python-dotenv` at startup, with `DJANGO_SECRET_KEY` (for Django) sourced exclusively from the environment, never hardcoded.

#### Scenario: Secret key sourced from environment
- **WHEN** the Django settings module is inspected
- **THEN** `SECRET_KEY` is read from `os.environ["DJANGO_SECRET_KEY"]` (or equivalent), with no literal secret value committed to source control
