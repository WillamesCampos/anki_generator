## ADDED Requirements

### Requirement: Login and Home screens use dedicated CSS files with design tokens
The system SHALL style `LoginPage` and `HomePage` through dedicated `.css` files consuming design tokens, matching the pattern already used by every other component, instead of inline `style` objects.

#### Scenario: LoginPage renders without inline style objects
- **WHEN** `LoginPage.jsx` is inspected
- **THEN** it contains no `style={{...}}` usage; visual styling comes from `LoginPage.css`

#### Scenario: HomePage renders without inline style objects
- **WHEN** `HomePage.jsx` is inspected
- **THEN** it contains no `style={{...}}` usage; visual styling comes from `HomePage.css`

#### Scenario: Visual appearance is unchanged
- **WHEN** the migration to dedicated CSS is complete
- **THEN** both screens look the same as before — this is a refactor, not a redesign
