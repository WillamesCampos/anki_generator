## ADDED Requirements

### Requirement: Anki package IDs are stable across exports of the same deck
The `document-generator` SHALL accept a `deck_id` and, per card, an `id` in `POST /document-generator/v1/decks/export`. It SHALL derive the Anki deck id deterministically from `deck_id`, use a fixed model id defined in code (changed only together with the export-format version), and derive each note's guid from the card `id`. The content hash used for caching SHALL NOT influence these IDs. Audio media file names SHALL be deterministic (derived from the card's front text) and not duplicated in the package's media list.

#### Scenario: Re-exporting an edited deck keeps the same Anki identity
- **WHEN** the same `deck_id` is exported twice with different card content
- **THEN** both packages carry the same deck id, the same model id and, for cards with the same `id`, the same note guids, so importing the second into Anki updates the existing deck instead of creating a duplicate

#### Scenario: Different decks never share an identity
- **WHEN** two different `deck_id` values are exported
- **THEN** their Anki deck ids differ

### Requirement: Export size is capped at 100 cards
The `document-generator` SHALL reject an export request with more than 100 cards (and with zero cards) with a client error, independently of validation done by the caller.

#### Scenario: Request above the cap is rejected
- **WHEN** an authenticated caller sends more than 100 cards to `POST /document-generator/v1/decks/export`
- **THEN** the service responds with a client error and generates nothing

### Requirement: Concurrent exports never share files
Each export request SHALL generate its audio files and `.apkg` inside a working directory unique to that request, and remove that directory after the response has been sent. Two concurrent requests, including requests with the same deck title, SHALL never read or overwrite each other's files.

#### Scenario: Same title, concurrent requests
- **WHEN** two requests with decks of the same title are processed at the same time
- **THEN** each response contains only the cards of its own request

#### Scenario: Working files are cleaned up
- **WHEN** an export response has been sent
- **THEN** the request's working directory no longer exists on the service's volume

### Requirement: Export generation does not block the service
The export route SHALL run the (synchronous, network-bound) generation outside the event loop, so other routes such as the health check keep responding while a generation is in progress.

#### Scenario: Health check during a long generation
- **WHEN** an export is being generated
- **THEN** a concurrent request to the health route is answered without waiting for the export to finish
