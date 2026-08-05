# Changelog

Todas as alterações relevantes do projeto são registradas aqui, conforme `<regra_obrigatoria id="changelog">` em [PROMPT_REFINADO.md](./PROMPT_REFINADO.md).

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
