## ADDED Requirements

### Requirement: Authenticated users trigger deck export asynchronously
The system SHALL expose `POST /api/v1/decks/{deck_id}/export/`, scoped to a deck the authenticated user owns. The endpoint SHALL never call the `document-generator` microservice synchronously within the request-response cycle. It SHALL respond `202 Accepted` with an `export_id` when a generation was enqueued or is already in progress, and `200 OK` with an `export_id` when an up-to-date export already exists (see "Export results are cached by content hash"). Only the deck's active cards (no `deleted_at`) SHALL be exported and counted.

#### Scenario: User triggers export of their own deck
- **WHEN** an authenticated user calls `POST /api/v1/decks/{deck_id}/export/` for a deck they own whose content has no existing export
- **THEN** the system responds `202` with an `export_id`, and the request returns before any call to `document-generator` is made

#### Scenario: Cross-tenant export request is rejected without leaking existence
- **WHEN** an authenticated user calls `POST /api/v1/decks/{deck_id}/export/` for a `deck_id` that exists but belongs to another user
- **THEN** the system returns `404`, never triggering an export and never distinguishing "deck exists but isn't yours" from "deck doesn't exist"

#### Scenario: Deck without active cards is refused up front
- **WHEN** the user triggers an export for a deck that has zero active cards
- **THEN** the system responds `400` with a clear message and enqueues nothing

#### Scenario: Deck above the size cap is refused up front
- **WHEN** the user triggers an export for a deck with more than 100 active cards
- **THEN** the system responds `400` explaining the 100-card limit and enqueues nothing

#### Scenario: Soft-deleted cards are not exported
- **WHEN** a deck has cards with `deleted_at` set
- **THEN** those cards are neither counted toward the 100-card cap nor included in the exported payload

### Requirement: Export results are cached by content hash
The system SHALL compute a `content_hash` (sha256 of a canonical serialization) over exactly the payload that would be sent to the `document-generator`: an export-format version constant, the deck title, and the active cards in a deterministic order with their `id`, `front`, `back`, `front_description`, `back_description` and `notes`. Spaced-repetition (FSRS) state SHALL NOT be part of the hash. The system SHALL keep, per `(owner_id, deck_id, content_hash)`, an index in Redis pointing to the export, and the exported object SHALL be stored in S3 under `exports/{owner_id}/{deck_id}/{content_hash}.apkg`. The cache SHALL never be shared across tenants.

#### Scenario: Unchanged deck is served from cache
- **WHEN** the user triggers an export for a deck whose content hash already has a completed export
- **THEN** the system responds `200` with that export's `export_id`, enqueues no task and makes no call to `document-generator`

#### Scenario: Editing the deck invalidates the cache
- **WHEN** the user changes a card's exportable field, adds a card, soft-deletes a card, or renames the deck, and then triggers an export
- **THEN** the content hash differs, no cache entry matches, and a new generation is enqueued (`202`)

#### Scenario: Studying a card does not invalidate the cache
- **WHEN** the user reviews cards of a deck (`POST /api/v1/cards/{card_id}/review/`) after an export completed, and then triggers an export again
- **THEN** the content hash is unchanged and the system responds `200` from cache

#### Scenario: Concurrent identical requests share one generation
- **WHEN** the user triggers an export for a deck while an export of the same content hash is still in progress
- **THEN** the system responds `202` with the `export_id` of the in-progress export and does not enqueue a second task

#### Scenario: Identical content of two tenants is never shared
- **WHEN** two different users export decks whose content is identical
- **THEN** each gets its own generation and its own S3 object, scoped by `owner_id`

### Requirement: Export task generates the .apkg and stores it in S3
The Celery task SHALL receive a snapshot of the payload and its `content_hash` as arguments (it SHALL NOT re-read the deck from the database), call the `document-generator` microservice using the existing service JWT infrastructure, receive the generated `.apkg` binary, and upload it to the private S3 bucket at `exports/{owner_id}/{deck_id}/{content_hash}.apkg`. On success it SHALL mark the export record `completed` with the S3 key. On any failure it SHALL mark the record `failed`, upload nothing, and release the content index so the export can be retried.

#### Scenario: Export task completes successfully
- **WHEN** the Celery task successfully calls `document-generator` and uploads the resulting `.apkg` to S3
- **THEN** the export record reports `status: completed` along with the S3 key, and the content index is kept for reuse

#### Scenario: Export task fails after exhausting resilience mechanisms
- **WHEN** the call to `document-generator` fails even after retry and circuit breaker handling (see `microservice-call-resilience`)
- **THEN** the export record reports `status: failed`, no S3 upload is attempted, and a later export request for the same content enqueues a new attempt

#### Scenario: Deck edited while the task is queued
- **WHEN** the deck is edited after the request was accepted but before the task runs
- **THEN** the task still generates and stores exactly the snapshot described by its `content_hash`, never newer content under the old hash

### Requirement: Pending state outlives queue wait and execution
The `pending` record and content index SHALL be created with a TTL that covers the time the task waits in the queue, and SHALL be renewed when the task starts, so the record cannot expire while the task may still be running. If the record no longer exists when the task starts, the task SHALL finish without generating anything.

#### Scenario: Task waits in the queue longer than the pending TTL
- **WHEN** the task starts after its `pending` record has already expired
- **THEN** the task ends without calling `document-generator` and without uploading anything

#### Scenario: Task start renews the record
- **WHEN** the task starts and its `pending` record exists
- **THEN** the record and the content index get a renewed `pending` TTL

### Requirement: Frontend polls export status and receives a scoped download link
The system SHALL expose `GET /api/v1/decks/export/{export_id}/status/`, returning the export's status (`pending`, `completed`, `failed`) read from a Redis record created at dispatch time and holding the `owner_id`. When `completed`, the response SHALL include a presigned S3 download URL generated fresh on each call (local signing, no S3 network call), with a 15-minute expiration, never persisted or logged. The endpoint SHALL respond `404` when the record does not exist, has expired, or belongs to another user, with an identical response in the three cases.

#### Scenario: Owner polls a completed export
- **WHEN** the authenticated user who triggered the export calls the status endpoint after it completed
- **THEN** the response reports `status: completed` and includes a freshly generated presigned URL valid for 15 minutes

#### Scenario: Owner polls a pending export
- **WHEN** the authenticated user who triggered the export calls the status endpoint before the task finished
- **THEN** the response reports `status: pending` with no download URL

#### Scenario: Owner polls a failed export
- **WHEN** the export task failed
- **THEN** the response reports `status: failed` with no download URL

#### Scenario: Another user cannot poll someone else's export
- **WHEN** an authenticated user calls the status endpoint with an `export_id` that belongs to another user's export, including while it is still `pending`
- **THEN** the system returns `404`, never revealing the export's status or a download URL

#### Scenario: Unknown or expired export id is a terminal 404
- **WHEN** a user polls an `export_id` that never existed or whose record expired
- **THEN** the system returns `404` (the same response as for another tenant's id), so a client never polls forever

### Requirement: Exported artifacts and their cache expire together
The system SHALL configure an S3 lifecycle rule expiring objects under `exports/` after 7 days. Completed export records and their content index in Redis SHALL expire 6 days after completion, so an index never points to an object already removed by the lifecycle rule. After expiry the user simply triggers a new generation. A `failed` record SHALL expire in a short time and a `pending` record SHALL carry a safety TTL longer than the longest possible task duration, so a crashed worker cannot lock a content hash indefinitely.

#### Scenario: Export older than the cache window is regenerated
- **WHEN** a user triggers an export for content whose Redis index has expired
- **THEN** the system treats it as a cache miss and enqueues a new generation

#### Scenario: A crashed worker does not lock the export forever
- **WHEN** a worker dies while an export is `pending`
- **THEN** after the safety TTL the record and content index disappear and the user can trigger the export again
