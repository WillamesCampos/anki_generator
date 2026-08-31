## Why

O domínio migrado na Sprint 0 (`django/apps/decks/`) ainda reflete o protótipo antigo (gerador de vocabulário via IA): não tem isolamento multi-tenant, não tem nenhum campo de agendamento de repetição espaçada, e não tem como registrar se um card foi acertado ou errado numa revisão. Sem isso, o produto não tem dado real de estudo — é a funcionalidade central sem a qual nada mais no roadmap (dashboard, agente de IA, relatórios) tem o que consumir.

## What Changes

- Adiciona `owner_id` a `Deck` e `Card` (Mongo) e um mecanismo de filtro de tenant equivalente ao `TenantOwnedModel`, mas implementado na camada de repositório Motor (sem ORM).
- Adiciona campos de agendamento de repetição espaçada ao `Card`, usando o algoritmo FSRS (via pacote `fsrs`) em vez de SM-2 manual.
- Introduz a entidade `CardReview` (evento de revisão por card: timestamp, rating, resultado do agendamento) — deliberadamente **não** reaproveita/renomeia `GenerationSession` (que continua representando um job de geração de cards via IA, conceito diferente).
- Cria a entidade `Category` do zero (não existe hoje no domínio migrado) — `Deck` ganha `category_id`; `Card` ganha `tags: List[str]` — cobrindo o índice de "categoria/tag" exigido pelo PRD (tarefa 2.4).
- Endpoints REST versionados (`/api/v1/`) de CRUD para `Deck`, `Category` e `Card`, via Generic Views do DRF com `serializers.Serializer` manuais (não `ModelSerializer`) e `get_queryset()` retornando listas já resolvidas pelo repositório — com `APIView` pontual onde o padrão genérico não encaixa (ex.: registrar uma revisão, que é uma ação de domínio, não um CRUD).
- Views permanecem síncronas e chamam os repositórios Motor por uma ponte com event loop persistente — sem adoção de `adrf`/views assíncronas. A implementação inicial por `asgiref.async_to_sync` foi substituída na Sprint 7 após falhar sob concorrência real.
- Índices Mongo obrigatórios em `owner_id`, `deck_id` e `category`/tags.
- `management command` de seed (múltiplos usuários, decks/categorias, cards com histórico de revisão em datas variadas), protegido contra execução em produção, com suporte a `--reset`, usando `asyncio.gather` para as inserções concorrentes.
- Diagrama Mermaid da arquitetura atualizada do projeto (Django + microsserviços + bancos), incluído no `design.md`.

## Capabilities

### New Capabilities
- `deck-card-multi-tenant-isolation`: isolamento por `owner_id` em todas as queries Mongo de deck/card, mecanismo próprio (sem depender do `TenantOwnedModel` da Sprint 1, que é ORM/Postgres-only).
- `deck-card-crud-api`: endpoints REST versionados de CRUD para decks, categorias e cards sobre dado Mongo, via Generic Views do DRF adaptadas a repositório assíncrono.
- `spaced-repetition-scheduling`: campos e lógica de agendamento de repetição espaçada no `Card`, usando FSRS.
- `card-review-tracking`: registro de eventos de revisão (`CardReview`) por card, base para estatísticas futuras (Sprint 3).
- `decks-seed-command`: management command de seed multi-tenant, idempotente/`--reset`, protegido contra produção.

### Modified Capabilities
(nenhuma — Sprint 1 não definiu specs sobre o domínio de deck/card; não há requisito existente sendo alterado)

## Impact

- `django/apps/decks/domain/`: novos campos em `Card`/`Deck` (owner, agendamento, `tags`/`category_id`), novas entidades `Category` e `CardReview`.
- `django/apps/decks/infrastructure/`: repositórios Motor ganham filtro obrigatório por `owner_id` e índices novos; novos repositórios para `Category` e `CardReview`.
- `django/apps/decks/` (views/serializers/urls): novos endpoints REST versionados.
- `django/apps/decks/management/commands/`: novo comando de seed.
- `pyproject.toml`/Poetry (django): nova dependência `fsrs`.
- Nenhum impacto nos microsserviços FastAPI ou no domínio de `accounts` (Sprint 1).
