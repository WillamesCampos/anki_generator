## ADDED Requirements

### Requirement: Django as the primary backend
The system SHALL provide a Django project named `core` as the primary backend, with all feature apps located under an `apps/` directory, replacing the current FastAPI-as-primary setup.

#### Scenario: Django project boots successfully
- **WHEN** the Django development server is started (`python manage.py runserver` or equivalent Make target)
- **THEN** the server starts without errors and serves at least one working endpoint (e.g., an admin or health endpoint)

#### Scenario: New feature app follows the apps/ convention
- **WHEN** a new Django app is created for a product capability (e.g., decks, cards)
- **THEN** it is created inside `apps/<app_name>/` and registered in `core` settings, not at the project root

### Requirement: Existing FastAPI service reclassified as a satellite microservice
The FastAPI application currently at `presentation/api/` SHALL be reclassified as one of the FastAPI microsatellite services (document generation / Anki export) rather than the system's primary entrypoint, and SHALL be relocated accordingly.

#### Scenario: FastAPI service runs independently of Django
- **WHEN** the document-generation FastAPI service is started on its own
- **THEN** it boots and serves its endpoints without requiring the Django process to be running

#### Scenario: Django is the sole primary entrypoint
- **WHEN** a client (frontend or external system) needs authentication, user data, or multi-tenant business logic
- **THEN** it talks to the Django backend, never directly to a FastAPI microservice for these concerns

### Requirement: No dedicated microservice for charts/statistics
Charts and statistics SHALL be rendered client-side in the React SPA, consuming data already exposed by Django REST API endpoints. The system SHALL NOT introduce a dedicated FastAPI microservice (e.g., Plotly-based) for this purpose.

#### Scenario: Chart data request
- **WHEN** the frontend needs data to render a chart (e.g., cards studied, correct vs. incorrect)
- **THEN** it fetches that data from a Django REST API endpoint and renders the chart client-side, with no server-side chart-generation service involved

### Requirement: Service boundaries and communication contract are documented
The system SHALL have a documented system-design artifact defining the boundaries between Django and each FastAPI microservice, and how they communicate (synchronous HTTP calls vs. asynchronous messaging), before feature implementation begins in either.

#### Scenario: New microservice added
- **WHEN** a new FastAPI microservice is proposed (e.g., WhatsApp integration, AI agent)
- **THEN** its boundary and communication contract with Django is documented before code is written for it
