## ADDED Requirements

### Requirement: Home screen shows the last studied deck
The system SHALL display, on the Home screen, the deck the authenticated user most recently studied, sourced from the Django API.

#### Scenario: User with review history sees their last deck
- **WHEN** the authenticated user has at least one `CardReview` recorded
- **THEN** the Home screen shows the deck associated with the most recent review

#### Scenario: User with no review history sees an empty state
- **WHEN** the authenticated user has no `CardReview` recorded yet
- **THEN** the Home screen shows an empty/onboarding state instead of an error

### Requirement: Home screen shows study goal progress
The system SHALL display a study goal and the percentage of that goal already achieved by the authenticated user.

#### Scenario: Goal progress renders as a percentage
- **WHEN** the Home screen loads for an authenticated user
- **THEN** it shows the goal and the achieved percentage, computed from data available via the Django API

### Requirement: Home screen shows a statistics chart rendered client-side
The system SHALL render a statistics chart on the Home screen, computed and drawn client-side (Chart.js) from data fetched via the Django API — no chart image is generated server-side.

#### Scenario: Chart renders from live API data
- **WHEN** the Home screen loads
- **THEN** the chart is populated from the authenticated user's data returned by the Django API, not from static/mock data

### Requirement: Statistics chart can be exported to PDF
The system SHALL let the user export the Home screen's statistics chart as a PDF file, generated client-side.

#### Scenario: User exports the chart
- **WHEN** the user triggers the export action on the statistics chart
- **THEN** a PDF file is generated client-side containing the chart, downloadable without a server round-trip
