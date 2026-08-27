## Why

Auditoria via `backend-mentor` (verificada por grep/leitura de código, não suposição) encontrou que duas regras mandatórias de `PROMPT_REFINADO.md`, declaradas desde a Sprint 0/1, nunca foram de fato implementadas: `permissoes-django` (autorização via `Permission`/`Group` nativos) e `auditoria` (`created_by`/`updated_by`). Hoje `DEFAULT_PERMISSION_CLASSES` é só `IsAuthenticated` em toda view, sem nenhuma checagem de grupo/permissão; e `Deck`/`Card`/`Category`/`CardReview` não têm `created_by`/`updated_by` — o `AuditMixin`/`AuditSerializerMixin` da Sprint 1 existe só no app `accounts`, nunca usado pelas entidades de produto. O custo de fechar isso cresce com a superfície do sistema (mais endpoints a cada sprint); e a Sprint 10 (Agente de IA) já tem uma dependência dura disso — exige `created_by`/`updated_by = "ai_agent_machine"` em todo recurso criado pelo agente, campo que hoje nem existe.

Escopo ampliado via `backend-mentor` (mesma sprint, mesmo tema de "endurecer autenticação/autorização"): a chamada Django→microsserviço de documentos também está sem autenticação nenhuma hoje — `POST /document-generator/v1/decks/export` (`microservices/document-generator/app/routes/decks.py`) não checa nada, `CORSMiddleware(allow_origins=["*"])`, e a porta `8001` está publicada pro host no `docker-compose.yml` (exposição real no VPS, não hipotética). Esse item estava planejado dentro da Sprint 9 (integração Django↔microsserviço), mas foi movido pra cá — decisão explícita do usuário — porque é o mesmo tema de hardening desta sprint, e a Sprint 9 não precisa (nem deveria) definir o mecanismo de autenticação, só consumi-lo.

## What Changes

- `created_by`/`updated_by` adicionados a `Deck`, `Card`, `Category`, `CardReview` — preenchidos automaticamente pelos serializers manuais do domínio Mongo a partir da request autenticada, nunca aceitos como input do cliente.
- Grupo `standard_user` (Django `Group` nativo) atribuído automaticamente a todo usuário no signup e no comando de seed.
- `permission_classes` customizado, verificando pertencimento ao grupo, substituindo o `IsAuthenticated` puro em toda view de `decks`/`cards`/`categories`/`reviews`.
- **Decisão explícita de não fazer**: não criar `Permission` por model via `ContentType` sintético — `Deck`/`Card` não são `models.Model`, então não têm `ContentType`/migração automática. A autorização fica só em `Group` (rótulo grosso de capacidade), não em `Permission` granular por ação.
- Toda chamada Django→`document-generator` passa a levar um JWT de serviço (HS256) auto-assinado pelo Django, verificado localmente pelo FastAPI (sem round-trip/introspection). Segredo por par emissor↔verificador (não global), separado do `SIMPLE_JWT`/`DJANGO_SECRET_KEY` de usuário. Rotação sem downtime via `kid` versionado no header.
- **Decisão explícita de não fazer**: não usar OAuth2 `client_credentials` completo (`django-oauth-toolkit`) — resolveria só o lado emissor (exigiria Authorization Server via Django ORM) pra um único client interno controlado pelo próprio mantenedor; peso desproporcional ao problema real (identidade de serviço, não delegação a terceiros). Não usar secrets manager (Vault/Doppler) pra rotação — overengineering nesse estágio (projeto solo, VPS, poucos serviços internos, sem operação real que consuma rotação em tempo real).

## Capabilities

### New Capabilities
- `mongo-entity-audit-trail`: campos `created_by`/`updated_by` nas entidades de domínio Mongo (Deck/Card/Category/CardReview), preenchidos automaticamente pelos serializers.
- `group-based-authorization`: grupo `standard_user` + `permission_classes` customizado, substituindo `IsAuthenticated` puro nas views de decks/cards.
- `service-to-service-jwt-auth`: JWT de serviço auto-assinado (HS256, `kid` versionado) autenticando toda chamada Django→`document-generator`.

### Modified Capabilities
(nenhuma — nenhuma capability anterior foi arquivada em `openspec/specs/` cobrindo autorização/auditoria; os dois itens acima são capabilities novas)

## Impact

- Backend: `apps/decks/domain/entities/*.py` (novos campos), `apps/decks/serializers.py` (preenchimento automático), `apps/accounts/` (grupo `standard_user` criado via signal/data migration no signup, ou no `AbstractUser.save()`), `apps/decks/management/commands/seed_decks.py` (atribuir grupo aos usuários seedados), novo `permissions.py` em `apps/decks/` (ou local equivalente) com a `BasePermission` customizada.
- Nenhuma mudança de schema Postgres além do `Group`/`Permission` nativos já existentes (não precisa de migração nova, são tabelas do próprio `django.contrib.auth`).
- Sem impacto no frontend — é só uma checagem de autorização a mais no backend, transparente pro cliente que já está autenticado.
- Prepara terreno pra Sprint 10 (Agente de IA), que vai consumir tanto `created_by`/`updated_by = "ai_agent_machine"` quanto um futuro grupo `ai_agent` (não criado nesta sprint — YAGNI até o agente existir de verdade).
- Novo módulo de emissão de JWT de serviço no Django (client HTTP que chama o `document-generator` passa a assinar um token antes de cada request) e novo middleware/dependency de verificação em `microservices/document-generator/app/` (FastAPI) — segredo(s) compartilhado(s) via variável de ambiente em cada serviço (`.env` do Django e do `document-generator`), não em banco. Prepara terreno pra Sprint 9 (Exportação Anki), que só vai consumir esse mecanismo já pronto.
