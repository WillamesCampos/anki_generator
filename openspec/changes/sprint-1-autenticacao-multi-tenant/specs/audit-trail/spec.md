## ADDED Requirements

### Requirement: Abstract audit mixin
The system SHALL provide an abstract Django model mixin with `created_at`, `created_by`, `updated_at`, and `updated_by` fields, available for any future model to inherit (starting with Sprint 2's product models).

#### Scenario: Fields are optional at the database level
- **WHEN** the audit mixin's fields are inspected at the database level
- **THEN** `created_by`/`updated_by` allow null (per `PROMPT_REFINADO.md`'s existing rule), while still being populated automatically in the normal request flow

### Requirement: Audit fields populated automatically by serializers, never accepted from client input
The system SHALL populate `created_by`/`updated_by` from the authenticated request user inside the serializer layer, and SHALL reject or ignore any client-supplied value for these fields.

#### Scenario: Client attempts to set created_by directly
- **WHEN** a client sends a request payload that includes a `created_by` field with an arbitrary user ID
- **THEN** the system ignores the client-supplied value and sets `created_by` to the authenticated requesting user

#### Scenario: AI agent authorship (forward-looking)
- **WHEN** a resource is created through the AI agent's dedicated permission path (introduced in a future sprint)
- **THEN** the same mixin/mechanism is reused to set `created_by`/`updated_by` to `"ai_agent_machine"`, per `PROMPT_REFINADO.md`'s `<escopo_agente_ia>` — this requirement only establishes the mixin exists and is reusable, not the agent integration itself
