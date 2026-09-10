## Why

O acesso ao MongoDB hoje usa `motor` (driver assíncrono), o que obriga a existência de uma camada de ponte só para permitir que views, serializers e tasks **síncronos** do Django cheguem a repositórios `async def` (`apps/decks/infrastructure/async_bridge.py` + a lógica de amarração a event loop em `apps/decks/infrastructure/mongodb_connection.py`). Essa complexidade — thread dedicada com event loop próprio, reconexão por identidade de loop, lock do `asyncio` recriado por loop — só se justificaria se o projeto estivesse tirando proveito real de concorrência assíncrona no caminho de requisição. Não está: uma varredura por `asyncio.gather` em `apps/decks` só encontra uso em `management/commands/seed_decks.py` (script batch, fora do request/response), nenhuma view ou repositório faz fan-out concorrente de queries. Django continua em WSGI (sem plano de ir para ASGI — os serviços que precisam de async nativo são os microsserviços FastAPI/uvicorn, fora deste app). `pymongo` (driver síncrono, thread-safe nativamente, sem noção de event loop) já é dependência direta do projeto hoje, então a migração elimina uma classe inteira de complexidade sem adicionar nenhuma dependência nova.

## What Changes

- Trocar `AsyncIOMotorClient` (motor) por `pymongo.MongoClient` em toda a infraestrutura de persistência de `apps/decks`.
- **BREAKING** (interno, não afeta contrato de API pública): todos os repositórios de `apps/decks` (`CardRepository`, `CardReviewRepository`, `CategoryRepository`, `DeckRepository`, `GenerationSessionRepository`) e suas interfaces de domínio (`ICardRepository` etc.) deixam de ser `async def` e passam a ser métodos síncronos comuns.
- Remover por completo `apps/decks/infrastructure/async_bridge.py` (`PersistentAsyncExecutor`/`persistent_async_to_sync`) — nenhum consumidor mais precisa de ponte sync↔async.
- Simplificar `apps/decks/infrastructure/mongodb_connection.py`: `MongoDBConnectionManager` deixa de rastrear/comparar event loop (`self._loop`, `is_connected()` baseado em `current_loop is self._loop`) e o `asyncio.Lock` recriado por loop em `ensure_mongodb_connection()` vira um `threading.Lock` comum — conexão passa a ser lazy-connect thread-safe simples, sem nenhuma noção de loop.
- Atualizar todos os call sites em `apps/decks/views.py` e `apps/decks/serializers.py` (hoje envolvidos em `persistent_async_to_sync(...)`) para chamada direta e síncrona dos repositórios.
- Atualizar `apps/decks/tasks.py` (task Celery `purge_soft_deleted`) para chamar os repositórios diretamente, sem ponte.
- Reescrever `apps/decks/management/commands/seed_decks.py` e `migrate_card_fields.py` para a API síncrona do pymongo, substituindo o paralelismo via `asyncio.gather` por operação em lote (`insert_many`/`bulk_write`) onde fizer sentido para não perder desempenho de seed.
- Simplificar `apps/decks/tests/conftest.py`, removendo o wrapper `run_async`/`asyncio.run` hoje necessário para tocar as fixtures de Mongo.
- Remover a dependência `motor` de `django/pyproject.toml` (`pymongo` permanece, já presente).
- Nenhuma mudança de contrato observável da API REST (`/api/v1/...`): filtros por `owner_id`, soft delete, paginação e formato de resposta continuam idênticos — é uma migração de mecanismo de I/O, não de regra de negócio.

## Capabilities

### New Capabilities

- `deck-persistence-sync-io`: mecanismo de persistência síncrona (pymongo) para decks/cards/categories/reviews/generation-sessions, incluindo gestão de conexão (client singleton, lazy-connect thread-safe) e criação de índices — substitui o mecanismo assíncrono implícito hoje não formalizado em nenhuma spec.

### Modified Capabilities

_(nenhuma — não há specs existentes em `openspec/specs/` para este domínio; comportamento observável da API não muda, então não há delta de requisito a registrar em spec de API já existente)_

## Impact

- **Código afetado**: `apps/decks/domain/repositories/*.py` (5 interfaces), `apps/decks/domain/services/duplicate_detection_service.py`, `apps/decks/infrastructure/mongodb_connection.py`, `apps/decks/infrastructure/mongodb_config.py` (validar compatibilidade de kwargs entre os dois clients), `apps/decks/infrastructure/repositories/*.py` (5 repositórios), `apps/decks/views.py`, `apps/decks/serializers.py`, `apps/decks/tasks.py`, `apps/decks/management/commands/seed_decks.py`, `apps/decks/management/commands/migrate_card_fields.py`, `apps/decks/tests/conftest.py`.
- **Código removido**: `apps/decks/infrastructure/async_bridge.py` inteiro; toda lógica de loop/lock-por-loop em `mongodb_connection.py`.
- **Dependências**: remove `motor` de `django/pyproject.toml`; `pymongo` já presente, nenhuma dependência nova.
- **Testes**: suíte existente (Mongo real via `docker compose up -d mongo`, sem mocks) é o critério de aceite — nenhum teste deveria precisar mudar de asserção, só a forma de invocar (sem `asyncio.run`/`await`).
- **CI**: `.github/workflows/ci.yml` já sobe `mongo:7` como serviço real; sem mudança esperada no workflow.
- **Infra/deploy**: nenhum impacto em `Dockerfile`/`entrypoint.sh`/`docker-compose.yml` — Django continua servido via `manage.py runserver` (WSGI), sem relação com esta mudança.
- **Fora de escopo**: qualquer migração de Django para ASGI (não é o objetivo — decisão já tomada de manter WSGI); mudanças nos microsserviços FastAPI (permanecem async/uvicorn, não são afetados).
