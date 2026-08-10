# Changelog

Todas as alterações relevantes do projeto são registradas aqui, conforme `<regra_obrigatoria id="changelog">` em [PROMPT_REFINADO.md](./PROMPT_REFINADO.md).

## [Sprint 2] Decks & Cards (domínio core) — 2026-08-10

Primeira feature real sobre o domínio de deck/card migrado na Sprint 0, agora multi-tenant e com repetição espaçada. Ver `openspec/changes/sprint-2-decks-cards/`.

### Adicionado
- Isolamento multi-tenant em MongoDB: `owner_id` obrigatório em toda assinatura de método de repositório (`Deck`/`Category`/`Card`/`CardReview`), embutido diretamente no filtro da query — mecanismo próprio da camada Motor, já que o `TenantOwnedModel` da Sprint 1 é ORM/Postgres-only.
- Entidade `Category` (nova — não existia no domínio migrado); `Deck` ganhou `category_id`, `Card` ganhou `tags` e os campos de agendamento FSRS (`stability`, `difficulty`, `due_at`, `fsrs_state`).
- Repetição espaçada via FSRS (pacote `fsrs`, o mesmo algoritmo do Anki real desde 2023) — `domain/services/scheduling_service.py`.
- Entidade `CardReview` — um documento por evento de revisão (mesma granularidade do `revlog` do Anki), deliberadamente distinta de `GenerationSession` (que continua representando só o job de geração de cards via IA).
- Endpoints REST versionados (`/api/v1/decks/`, `/categories/`, `/cards/`, `/cards/{id}/review/`) via Generic Views do DRF sobre repositório Motor — serializers `serializers.Serializer` manuais (não `ModelSerializer`), `get_queryset()` retornando lista já resolvida via `async_to_sync`; `APIView` dedicada para a ação de revisão (não é CRUD).
- Índices Mongo por `owner_id`/`deck_id`/`category_id`/`tags`/`due_at`, definidos em `IndexDefinitions` (`schemas.py`) — agora fonte única também para `MongoDBConnectionManager.create_indexes()` (antes havia uma segunda lista hardcoded e divergente).
- Comando de seed multi-tenant (`seed_decks`): múltiplos usuários, decks/categorias/cards com tags, `CardReview` com datas passadas/recentes/futuras — entrypoint `asyncio.run` com `asyncio.gather` para inserções concorrentes reais (sem bridge `async_to_sync`), protegido contra produção (`settings.DEBUG`), suporte a `--reset`.
- 16 novos testes automatizados (isolamento cross-tenant contra Mongo real, CRUD dos endpoints, revisão/agendamento FSRS, cards devidos, guarda de produção do seed) — **28/28 passando** com a Sprint 1.
- Hierarquia de exceções própria do projeto (`core/exceptions.py`): `AppError`, base abstrata (não instanciável diretamente — nem `ABC` sozinho bloqueia isso em subclasses de `Exception`, foi preciso um guard manual). Duas ramificações: `DomainValidationError` (substitui todo `ValueError` cru levantado por entidades/objetos de valor) e `InfrastructureError` → `RepositoryError`/`CardNotFoundError`/`DeckNotFoundError`/`CategoryNotFoundError`/`SessionNotFoundError`/`MongoNotConnectedError`/`MongoConfigError` (substitui os `RuntimeError`/`ValueError` da camada Mongo). Consolidado em `apps/decks/infrastructure/exceptions.py`, corrigindo de passagem um layering estranho: `RepositoryError` vivia dentro de `card_repository.py` e todo outro repositório importava dela como se fosse módulo compartilhado.

### Corrigido
- **Bug real de produção, descoberto via verificação end-to-end com requests HTTP reais (não só testes unitários)**: `AsyncIOMotorClient` fica preso ao event loop em que foi criado; `asgiref.sync.async_to_sync` cria um event loop novo a cada chamada bridged, sem loop "principal" já rodando na thread. O singleton `MongoDBConnectionManager` e o cache de `_collection` por instância de repositório quebravam com `RuntimeError: Event loop is closed` já na segunda/terceira chamada do processo. Corrigido: `is_connected()` agora valida o loop atual e força reconexão quando diverge; repositórios pararam de cachear `_collection` na instância.
- `GenerationSessionRepository.find_by_id()` (Sprint 0) chamava `CardRepository.find_by_deck_id()` sem `owner_id` — quebrado pela mudança acima; `owner_id` agora é parâmetro explícito também nesse método.
- **Segundo bug real, também de produção, encontrado em revisão pré-commit**: `datetime.utcnow()` (deprecated) foi trocado por `datetime.now(timezone.utc)` em todo `apps/decks/` — mas o mais importante foi o que essa troca revelou: Motor/pymongo devolvem datetime *naive* na leitura (mesmo quando o valor foi inserido como aware), então revisar o mesmo card uma segunda vez (com `due_at`/`last_reviewed_at` vindos do Mongo) quebrava com `TypeError: can't subtract offset-naive and offset-aware datetimes` dentro do `fsrs.Scheduler`. Corrigido na fronteira `schemas.py`: novo helper `datetime_from_mongo()` reanexa o offset UTC em toda leitura, usado nos cinco schemas. Validado revisando o mesmo card 3x seguidas via API real.

### Qualidade de código (revisão pré-commit)
- Espaço em branco no fim de linha removido de 16 arquivos em `apps/decks/` (domínio + infraestrutura, código herdado da Sprint 0 nunca revisado antes).
- `seed_decks.py` reescrito para legibilidade: os `asyncio.gather(*( ... for ... ))` aninhados de 3 níveis viraram "monta a lista de objetos" → "salva tudo concorrentemente" como dois passos nomeados e separados, sem custo de performance; números mágicos (`2` decks por categoria, `4` cards por deck) viraram constantes nomeadas.

### Decisão de escopo
- Métodos/serviços legados do protótipo antigo de geração de vocabulário (`find_by_word`, `find_similar_cards`, `find_duplicates`, `exists_by_word`, `duplicate_detection_service`, `card_quality_service`) — não usados por nenhuma view/URL, não previstos no PRD — foram mantidos e escopados por `owner_id`, por decisão explícita do usuário, para o caso do agente de IA (Sprint 5) reaproveitar essa lógica.

## [Sprint 1] Autenticação & Multi-tenant — 2026-08-05

Primeira feature real do sistema, sobre a fundação da Sprint 0. Ver `openspec/changes/sprint-1-autenticacao-multi-tenant/`.

### Adicionado
- App `django/apps/accounts/`: model de usuário customizado (`email` único, `USERNAME_FIELD = "email"`), reaproveitando `AbstractUser`.
- Autenticação JWT (`djangorestframework-simplejwt`) com refresh token revogável via blocklist no Redis — logout tem efeito imediato, sem esperar a expiração natural do token.
- Login via Google OAuth (`django-allauth` + `dj-rest-auth`), exposto como endpoint REST (`/api/v1/auth/google/`) devolvendo JWT em vez de página HTML — decisão mentorada, justificada pela SPA (Sprint 3) ficar em origem separada (S3) da API Django.
- Isolamento multi-tenant reutilizável: `TenantOwnedModel`/`TenantOwnedQuerySet` (`apps/accounts/tenancy.py`) — qualquer model futuro herda em vez de reimplementar o filtro por usuário dono. Confirmado que "multi-tenant" neste projeto = isolamento por usuário, sem entidade `Organization`/`Tenant` separada.
- `AuditMixin`/`AuditSerializerMixin` (`apps/accounts/audit.py`): `created_at/by`, `updated_at/by` preenchidos automaticamente a partir do usuário autenticado, ignorando qualquer valor enviado pelo cliente.
- Rate limiting de 3 req/s por usuário/cliente via throttle classes do DRF, usando o Redis já configurado.
- Primeira infraestrutura de testes automatizados do projeto: pytest + pytest-django, 12 testes cobrindo isolamento multi-tenant, auditoria, rate limiting, permissões e o ciclo completo de refresh/logout do JWT.

### Corrigido
- `AUTH_USER_MODEL` definido antes de qualquer migration real ter sido aplicada com dados reais — única janela seguras para essa troca (documentado em design.md desta sprint).

### Pendências conhecidas
- `GOOGLE_OAUTH_CLIENT_ID`/`GOOGLE_OAUTH_CLIENT_SECRET` ainda não configurados com credenciais reais (requer criar um projeto OAuth no Google Cloud Console) — o fluxo de login com Google em si não foi validado ponta a ponta com o Google de verdade; toda a mecânica de emissão/revogação de JWT foi validada de forma independente.

## [Sprint 0] Fundação de arquitetura — 2026-08-04

Migração do monólito FastAPI incompleto para a arquitetura-alvo (Django como backend principal + microsserviços FastAPI satélites), conforme `openspec/changes/migrate-to-django-microservices-architecture/`.

### Adicionado
- Projeto Django (`django/core/` + `django/apps/decks/`), Python 3.13, Django 6, DRF, settings segregadas por ambiente (`local`/`production`), `python-dotenv` + `DJANGO_SECRET_KEY` via variável de ambiente.
- Domínio de deck/card/geração (`apps/decks/domain/`) e repositórios MongoDB via Motor (`apps/decks/infrastructure/`), consolidados a partir do protótipo anterior — com correção de um bug real de conversão `ObjectId ↔ UUID` que impedia `save`/`find_by_id` de funcionar.
- Microsserviço FastAPI de geração de documentos (`microservices/document-generator/`), com exportação `.apkg` (genanki + gTTS) validada end-to-end via container.
- `docker-compose.yml` na raiz: Django, PostgreSQL, MongoDB, Redis, RabbitMQ, Celery worker e o microsserviço de documentos — todos os containers de aplicação rodando com usuário non-root dedicado e `entrypoint.sh`.
- Fundação Celery + RabbitMQ (broker) + Redis (result backend/cache), sem tasks reais ainda.
- URLs versionadas (`/api/v1/...`) com endpoint de health check.
- `PRD.md` com roadmap completo do projeto em sprints.
- `frontend/` (placeholder da Sprint 3, ainda sem código).

### Alterado
- **Reorganização do monorepo por unidade implantável** (ver `<estrutura_monorepo>` em `PROMPT_REFINADO.md`): o Django, que estava espalhado solto na raiz (`core/`, `apps/`, `manage.py`, `pyproject.toml`, `Dockerfile`), passou para `django/`; `services/` foi renomeado para `microservices/` (evita colisão de nome com `apps/decks/domain/services/`, que já significa "serviços de domínio" em DDD). `docker-compose.yml` e `Makefile` continuam na raiz, atualizados para os novos caminhos (`poetry -C django ...`).
- `Makefile`: removido o alvo Postgres órfão (subia um container não usado por nenhum código); novos alvos `up`/`down`/`logs`/`migrate`/`makemigrations`/`run`.
- `pyproject.toml`: dependências FastAPI-específicas (genanki, gTTS, fastapi, uvicorn, pydantic-settings, sqlalchemy não utilizada) removidas — agora vivem em `microservices/document-generator/requirements.txt`; Python `^3.13`.
- `test_mongodb_integration.py` portado para `apps/decks/tests/`, roda a partir da raiz do projeto sem depender de `legacy/` no path.

### Removido
- `legacy/`, `presentation/`, `shared/`, `main.py`, `generator_v2.py` (raiz) — conteúdo reaproveitável migrado; o restante era duplicado ou não utilizado.

### Corrigido
- Bug de conversão `ObjectId → UUID` (e vice-versa) em `CardRepository`/`DeckRepository`/`GenerationSessionRepository`: o código original tentava construir um `uuid.UUID` diretamente a partir do hex de 24 caracteres de um `ObjectId` (que precisa de 32), o que fazia `save`/`find_by_id` falharem sempre. Nunca havia sido validado funcionando antes desta sprint.
