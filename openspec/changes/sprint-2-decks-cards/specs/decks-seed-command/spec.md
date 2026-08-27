## ADDED Requirements

### Requirement: Multi-tenant seed management command
The system SHALL provide a Django management command that seeds multiple users (tenants), each with varied decks/categories and cards, including `CardReview` history with past/recent/future dates, for local development and manual testing.

#### Scenario: Seed creates data across multiple owners
- **WHEN** the seed command runs
- **THEN** it creates records for more than one distinct user, each with their own decks/categories/cards, correctly scoped by `owner_id`

#### Scenario: Seed creates review history with varied dates
- **WHEN** the seed command runs
- **THEN** generated `CardReview` records include timestamps spanning past, recent, and future dates

### Requirement: Seed command uses real concurrency via asyncio.gather
The seed command SHALL run as a standalone async entrypoint (`asyncio.run`), using `asyncio.gather` to perform independent Mongo insertions concurrently, without going through a Django request/response cycle or an `async_to_sync` bridge.

#### Scenario: Independent inserts run concurrently
- **WHEN** the seed command inserts unrelated records (e.g. decks for different users)
- **THEN** those insertions are dispatched concurrently via `asyncio.gather`, not sequentially awaited one at a time

### Requirement: Seed command is blocked in production
The seed command SHALL refuse to run when the environment is identified as production (via the project's existing environment/debug configuration), to prevent accidental pollution of real data.

#### Scenario: Command exits without writing in production
- **WHEN** the seed command is invoked with the production environment configuration active
- **THEN** it exits immediately with an error, without performing any write to MongoDB

### Requirement: Seed command supports idempotent re-runs or explicit reset
The seed command SHALL either be safely re-runnable without duplicating data, or SHALL support an explicit `--reset` flag that clears previously seeded data before re-seeding.

#### Scenario: Re-running with --reset clears prior seed data
- **WHEN** the command is run a second time with `--reset`
- **THEN** previously seeded records are removed before new ones are created, leaving no duplicates

### Requirement: Automated tests cover the seed command and its production guard
The system SHALL include automated tests verifying both that the seed command produces the expected data shape and that it refuses to run in a production environment.

#### Scenario: Test verifies production guard
- **WHEN** the test suite simulates a production environment and invokes the seed command
- **THEN** the test asserts the command aborts and no data is written
