# Changelog

Todas as alterações relevantes do projeto são registradas aqui, conforme `<regra_obrigatoria id="changelog">` em [PROMPT_REFINADO.md](./PROMPT_REFINADO.md).

## [Sprint 3] Frontend Base & Home Dashboard — 2026-08-11

Primeira superfície visual do sistema. Ver `openspec/changes/sprint-3-frontend-base-home-dashboard/`.

### Adicionado
- `frontend/`: SPA React via Vite, `react-router` para navegação entre seções, camada de API client (`fetch` + hooks) apontando para `/api/v1/...` com anexação de JWT.
- Tokens de design (`frontend/src/tokens/`) extraídos por auditoria real de `refs/Ashley_files/style.css` (o CSS que `design_system/design-system.html` documenta — um template comercial de portfólio, não um design system de app) — cor, tipografia ("Outfit"), espaçamento, raio de borda, cada valor rastreável a uma linha do CSS original (`AUDIT.md`).
- Componentes base (`Sidebar`, `AppShell`, `Card`, `Button`) construídos do zero em React usando os tokens — não se importa o CSS do template diretamente.
- Tela Home: último deck estudado, meta de estudo + % alcançado (client-side), gráfico de distribuição de revisões por resultado (Chart.js/`react-chartjs-2`) e exportação desse gráfico para PDF (`jsPDF`, direto do canvas).
- Menu lateral (decks, categorias, relatórios, chat IA) — chat IA é só placeholder visual, sem chamada de API (agente real chega na Sprint 7).
- `GET /api/v1/reviews/` (backend) — histórico de `CardReview` do usuário autenticado, mais recentes primeiro; `CardReviewRepository.find_by_owner()` novo.
- Checklist de auditoria de consistência visual (`frontend/src/tokens/VISUAL_AUDIT.md`), executado contra o código real via grep — encontrou e corrigiu 2 desvios (espaçamento inline fora dos tokens em `HomePage.jsx`).
- `Makefile`: alvos `frontend-install`/`frontend-dev`/`frontend-build`/`frontend-lint`/`seed`.
- Tela de login (`/login`) com dois fluxos: e-mail/senha (`dj_rest_auth.views.LoginView`, novo em `apps/accounts/urls.py`) e Google OAuth2 (fluxo "token client" do Google Identity Services — não o botão "Sign In" mais novo, que devolve ID token em vez do `access_token` OAuth2 que o `GoogleOAuth2Adapter` do backend espera). Componente `Input` novo (`frontend/src/components/ui/`).
- Fluxo de refresh de token na SPA: `access` + `refresh` guardados no `localStorage`; em qualquer 401, `apiFetch` tenta renovar via `/auth/token/refresh/` (deduplicando chamadas concorrentes) antes de repetir a requisição original; só desloga (evento `auth:session-expired`) se o refresh também falhar. `AuthContext`/`useAuth()` novos.
- Botão de recolher/expandir a sidebar, estado persistido em `localStorage`.
- `seed_decks.py`: todo usuário seedado agora tem senha conhecida (`anki12345`, documentada em `frontend/README.md`) para permitir login e navegação autenticada de ponta a ponta sem depender de credenciais reais do Google.

### Corrigido (gap de escopo encontrado em implementação)
- A proposta original desta sprint previa "nenhum impacto no backend" — falso: a Sprint 2 persistia `CardReview` mas nunca expunha leitura via API, e a Home não tem como mostrar "último deck estudado"/gráfico de estatísticas sem esse histórico. Resolvido com o menor impacto possível: um método de repositório + uma Generic View reaproveitando tudo que a Sprint 2 já construiu, não um endpoint novo com lógica própria.
- **Corrigido também**: CORS nunca tinha sido configurado (`django-cors-headers` não era nem dependência) — a SPA (`:5173`) e a API (`:8000`) são origens diferentes, então o navegador bloqueava a SPA de ler qualquer resposta, mesmo com JWT válido. Adicionado, com `CORS_ALLOWED_ORIGINS` liberado só pra `localhost:5173` em dev e vazio por padrão (via env var) em produção.
- **Corrigido também**: `Deck.title` gerado pelo comando de seed usava um padrão genérico (`"Categoria — Deck N"`) sem servir como identificador amigável na Home — encontrado testando a Home de verdade, não em revisão de código. `seed_decks.py` agora gera título + descrição reais e variados por deck (`DECK_CATALOG`); a Home exibe `Deck.description` (campo já existente desde a Sprint 2, nunca populado) quando presente.
- **Corrigido também**: "último deck estudado" fazia `GET /cards/{id}/` seguido de `GET /decks/{id}/` (2 requests em cadeia) só pra descobrir o deck de uma revisão — combinado com o double-effect do React 18 StrictMode em dev (`GET /reviews/` disparado 2x), a cadeia completa de 4 requests estourava o throttle de 3 req/s, retornando 429 e travando o card em "Não foi possível carregar o deck". Corrigido denormalizando `deck_id` (referência estável, não um título — sem risco de ficar desatualizado) direto no `CardReview`, no momento da revisão — a SPA agora busca o deck em 1 request só.

### Alterado
- `SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]`: 15min (Sprint 1) → 1h — o fluxo de dev manual (sem tela de login, token colado no `localStorage`) tornava a duração curta original irritante de testar. Nenhum ajuste necessário no blocklist de refresh token: seu TTL no Redis já é calculado dinamicamente a partir do `exp` real de cada token, não um valor fixo espelhando `ACCESS_TOKEN_LIFETIME`.

### Corrigido (configuração do allauth para login por e-mail/senha)
- `ACCOUNT_LOGIN_METHODS` não estava setado — allauth 65.x, sem essa config, usa o default (login só por `username`), incompatível com o `LoginSerializer` do dj-rest-auth (que manda `{email, password}`) e com `User.USERNAME_FIELD = "email"`. Confirmado pelo erro real da API (`"Deve incluir 'username' e 'password'"`) e inspecionando `allauth.account.app_settings` diretamente. Corrigido com `ACCOUNT_LOGIN_METHODS = {"email"}`.
- `ACCOUNT_SIGNUP_FIELDS` setado inicialmente como dict (formato errado) — confirmado lendo o parser real do allauth (`SIGNUP_FIELDS`, que itera só as chaves de um dict, nunca encontra o sufixo `"*"`) que isso faz todo campo virar `required=False` silenciosamente. Formato correto é lista de strings (`["email*", "password1*", "password2*"]`).
- `seed_decks.py` deixava usuários seedados pré-existentes com senha efetivamente inutilizável: a condição original (`if created or not user.has_usable_password()`) nunca re-setava a senha em reruns, porque `Django.is_password_usable("")` retorna `True` (só checa o marcador `!` de `set_unusable_password()`, não string vazia). Corrigido setando a senha incondicionalmente a cada seed.

### Decisão de escopo
- "Meta de estudo" (tarefa 3.2) não tem nenhum modelo no backend — nunca foi definida em nenhum spec de produto o que uma meta significa (cards/dia? semana?). Em vez de inventar schema sem requisito real, fica em `localStorage` por enquanto (não persiste entre dispositivos) — decisão documentada explicitamente (D7 em `design.md`), não escondida.

### Pendências conhecidas
- Login funciona (e-mail/senha e Google), mas cadastro de conta nova e vínculo de conta (mesmo e-mail via Google e via senha) ainda não — levantamento de requisitos feito, decisão de escopo pendente (ver PRD.md 7.1).
- Bundle de produção (~720KB não comprimido no chunk principal, por causa de `jsPDF`+`html2canvas`+Chart.js) ainda sem code-splitting — aceitável no volume desta sprint, revisitar se o bundle crescer mais.

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
- Métodos/serviços legados do protótipo antigo de geração de vocabulário (`find_by_word`, `find_similar_cards`, `find_duplicates`, `exists_by_word`, `duplicate_detection_service`, `card_quality_service`) — não usados por nenhuma view/URL, não previstos no PRD — foram mantidos e escopados por `owner_id`, por decisão explícita do usuário, para o caso do agente de IA (Sprint 7) reaproveitar essa lógica.

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
