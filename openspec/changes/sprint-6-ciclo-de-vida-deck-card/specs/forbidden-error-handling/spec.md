## ADDED Requirements

### Requirement: The SPA shows a distinct message for permission-denied responses
The system SHALL treat HTTP `403` responses from the API distinctly from other errors in `apiFetch`, surfacing a clear "you don't have permission" message instead of the generic technical error text.

#### Scenario: API returns 403 for a group-denied request
- **WHEN** the SPA receives a `403` response from any API call
- **THEN** the UI shows a permission-denied message, not the generic error message used for other failures

#### Scenario: 403 is not confused with 401
- **WHEN** the SPA receives a `403` response
- **THEN** it does not trigger the token-refresh flow reserved for `401`, since the user is authenticated but simply not authorized
