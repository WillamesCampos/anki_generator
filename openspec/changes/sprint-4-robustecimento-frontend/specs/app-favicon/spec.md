## ADDED Requirements

### Requirement: The application has a browser tab icon
The system SHALL serve a favicon referenced from `index.html`, so the browser tab shows an icon instead of the default blank/generic one.

#### Scenario: Favicon is present on load
- **WHEN** the SPA is loaded in a browser
- **THEN** the browser tab displays the application's favicon, not a blank or default icon
