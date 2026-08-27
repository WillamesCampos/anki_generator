## ADDED Requirements

### Requirement: The deck form offers a category selector populated from existing categories
The system SHALL populate the deck form's category selector with the authenticated user's existing categories.

#### Scenario: Existing categories appear in the selector
- **WHEN** an authenticated user with existing categories opens the deck creation or edit form
- **THEN** the category selector lists those categories

### Requirement: Users can create a category inline from the deck form
The system SHALL allow creating a new category directly from the deck form's category selector, without leaving the form, and SHALL select the newly created category automatically.

#### Scenario: New category is created and selected inline
- **WHEN** an authenticated user chooses to create a new category from the deck form and submits a valid name
- **THEN** the category is created and becomes the selected value in the deck form's category selector
