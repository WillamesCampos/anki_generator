## ADDED Requirements

### Requirement: Versioned REST endpoints for Deck, Category, and Card
The system SHALL expose versioned REST endpoints (`/api/v1/...`) providing CRUD operations for `Deck`, `Category`, and `Card`, backed by the MongoDB repositories rather than the Django ORM.

#### Scenario: Deck CRUD is reachable under the versioned prefix
- **WHEN** a client sends `GET`, `POST`, `PUT`/`PATCH`, or `DELETE` to `/api/v1/decks/` (or `/api/v1/decks/{id}/`)
- **THEN** the request is routed to a Django view backed by `DeckRepository`

#### Scenario: Category is a first-class CRUD resource
- **WHEN** a client sends a request to `/api/v1/categories/`
- **THEN** the system creates, lists, updates, or deletes `Category` records scoped to the requesting user

### Requirement: Plain Serializer classes with manual create/update, not ModelSerializer
Serializers for `Deck`, `Category`, and `Card` SHALL be plain `rest_framework.serializers.Serializer` subclasses with explicit `create()`/`update()` methods delegating to the corresponding repository — `ModelSerializer` SHALL NOT be used, since no Django ORM model backs these resources.

#### Scenario: Serializer create() calls the repository, not the ORM
- **WHEN** a `DeckSerializer.save()` is invoked on a new instance
- **THEN** its `create()` method calls `DeckRepository`'s insert method, not `Model.objects.create()`

### Requirement: Generic Views over a repository-backed queryset
List/detail endpoints SHALL use DRF Generic Views (e.g. `ListCreateAPIView`, `RetrieveUpdateDestroyAPIView`) whose `get_queryset()` returns a plain Python list already resolved from the repository — preserving the project's mandatory rule to prefer Generic Views, adapted to non-ORM data.

#### Scenario: Pagination works over a plain list
- **WHEN** `GET /api/v1/decks/` is called with more decks than one page size
- **THEN** the response is paginated correctly using the list returned by `get_queryset()`, without requiring a Django `QuerySet`

### Requirement: APIView for non-CRUD domain actions
Actions that are not a CRUD state replacement (e.g. registering a card review, which triggers spaced-repetition scheduling) SHALL be implemented as plain `APIView` subclasses rather than forced into a Generic View.

#### Scenario: Review action is a dedicated endpoint
- **WHEN** a client sends `POST /api/v1/cards/{id}/review/`
- **THEN** the request is handled by a dedicated `APIView`, not a Generic View update endpoint

### Requirement: Views remain synchronous, bridging to Motor through a persistent event loop
Django views for deck/card/category endpoints SHALL remain synchronous (`def`, not `async def`), calling the Motor-based repositories through the process-local persistent async bridge.

#### Scenario: View function is a regular sync function
- **WHEN** a deck/category/card view is inspected
- **THEN** its handler methods are defined with `def`, and repository calls execute on the persistent bridge
