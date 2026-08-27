## ADDED Requirements

### Requirement: Authorization built on native Django Permission/Group
The system SHALL implement all authorization logic using Django's native `Permission` and `Group` models, and SHALL NOT introduce a parallel/custom permission system.

#### Scenario: New permission needed
- **WHEN** a new authorization rule is needed for a resource
- **THEN** it is expressed as a Django `Permission` (custom or built-in) checked via DRF permission classes, not as a bespoke boolean field or ad-hoc role string

#### Scenario: No parallel permission table exists
- **WHEN** the codebase/database schema is inspected for authorization logic
- **THEN** only `auth.Permission` and `auth.Group` (or their standard relations) are used to express who can do what
