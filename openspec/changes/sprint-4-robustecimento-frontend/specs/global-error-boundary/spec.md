## ADDED Requirements

### Requirement: An unhandled render error shows a fallback screen, not a blank page
The system SHALL wrap the application in a top-level error boundary that renders a simple fallback UI when a child component throws during render, instead of leaving the user with a blank screen.

#### Scenario: A component throws during render
- **WHEN** any component in the tree throws an unhandled error during render
- **THEN** the user sees a fallback screen with a clear message, not a blank page

#### Scenario: Normal rendering is unaffected
- **WHEN** no component throws
- **THEN** the application renders exactly as it did before the error boundary was added
