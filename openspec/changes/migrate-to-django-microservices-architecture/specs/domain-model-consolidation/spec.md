## ADDED Requirements

### Requirement: Single canonical domain layer
The system SHALL have exactly one canonical domain layer (entities, value objects, repository interfaces, domain services) for deck/card/generation-session concepts, migrated from the clean-architecture version currently orphaned under `legacy/domain/` and `legacy/infrastructure/`. The older flat domain structure (`legacy/domain/models.py`, `legacy/services/anki_deck_generator/`) SHALL be discarded.

#### Scenario: No duplicate domain definitions
- **WHEN** the codebase is searched for `Card`, `Deck`, or `GenerationSession` entity definitions
- **THEN** exactly one definition of each is found, reachable from the project root (not inside `legacy/`)

#### Scenario: Legacy directory removed after migration
- **WHEN** domain migration is complete and validated
- **THEN** the `legacy/` directory no longer exists in the repository

### Requirement: MongoDB repositories reachable from the new architecture
The Motor-based MongoDB repository implementations (`CardRepository`, `DeckRepository`, `GenerationSessionRepository`) SHALL be migrated into the new `apps/` structure and be importable and usable by the corresponding Django app, without needing `legacy/` on the Python path.

#### Scenario: Integration test runs from project root
- **WHEN** the MongoDB integration test (equivalent to the current `test_mongodb_integration.py`) is run from the project root using only root-level packages
- **THEN** it passes, performing CRUD operations against MongoDB through the migrated repositories

### Requirement: Reusable card/audio generation logic integrated
The genanki + gTTS card and audio generation logic proven in `generator_v2.py` SHALL be integrated into the consolidated domain/service layer (or the document-generation microservice, per the D1 architecture decision) rather than existing as a disconnected standalone script.

#### Scenario: Deck export triggered through the system
- **WHEN** a deck export is requested through the consolidated architecture (API call or internal service call, not by running `generator_v2.py` manually)
- **THEN** a valid `.apkg` file is produced using the same generation logic previously proven in `generator_v2.py`
