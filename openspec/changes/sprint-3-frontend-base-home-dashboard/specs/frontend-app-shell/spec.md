## ADDED Requirements

### Requirement: SPA scaffold built with Vite and React
The system SHALL provide a React SPA scaffolded with Vite, replacing the `frontend/` placeholder, buildable for production via a single command.

#### Scenario: Dev server runs locally
- **WHEN** a developer runs the frontend's dev command inside `frontend/`
- **THEN** a local dev server starts and serves the SPA with hot module reload

#### Scenario: Production build succeeds
- **WHEN** the frontend's build command is run
- **THEN** a static production bundle is produced, deployable to the S3 bucket decided in Sprint 0 (`hospedagem-frontend`)

### Requirement: Client-side routing across app sections
The system SHALL use `react-router` to navigate between sections (Home, decks, categories, reports, AI chat placeholder) without full page reloads.

#### Scenario: Navigating via the sidebar changes the route
- **WHEN** a user clicks a sidebar navigation item
- **THEN** the URL changes and the corresponding view renders, without a full browser reload

### Requirement: Thin API client layer for the Django backend
The system SHALL provide a single, reusable layer for calling the Django REST API (`/api/v1/...`), using native `fetch` and React hooks — no data-fetching/caching library (e.g. React Query) is introduced in this sprint.

#### Scenario: API calls share a common base configuration
- **WHEN** any part of the SPA calls the Django API
- **THEN** it goes through the shared API client layer (base URL, auth header attachment), not an ad-hoc `fetch` call duplicated per component
