## ADDED Requirements

### Requirement: Design tokens extracted from the reference stylesheet
The system SHALL provide a single design-tokens source (color palette, typography, spacing scale) extracted from `refs/Ashley_files/style.css` (the file `design_system/design-system.html` documents), used by every React component — no color, font, or spacing value SHALL be introduced outside this source.

#### Scenario: Token file traces back to the reference CSS
- **WHEN** the design-tokens file is inspected
- **THEN** every value (color, font-family, spacing) matches a value verifiably present in `refs/Ashley_files/style.css`, not an invented or approximated value

#### Scenario: Components consume tokens, not hardcoded values
- **WHEN** any new React component under `frontend/` declares a color, font, or spacing value
- **THEN** it references the shared design-tokens source rather than a literal hardcoded value

### Requirement: Visual consistency audit checklist
The system SHALL provide a checklist (manual or automated) comparing implemented screens against the extracted design tokens, satisfying acceptance criterion 12 in `PROMPT_REFINADO.md`.

#### Scenario: Audit catches a token deviation
- **WHEN** a screen is checked against the audit checklist
- **THEN** any color/font/spacing not traceable to the design-tokens source is flagged before the screen is considered done
