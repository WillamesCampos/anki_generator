## Context

Verificado por grep direto no código (não suposição): `grep -rn "permission_classes" apps/` só encontra `IsAuthenticated` (accounts) e `AllowAny` (health check); nenhuma view de `decks`/`cards`/`categories`/`reviews` tem `permission_classes` além do default global. `grep -rn "created_by\|updated_by" apps/decks/` não encontra nada — as entidades de domínio (`Deck`, `Card`, `Category`, `CardReview`, todas dataclasses em `apps/decks/domain/entities/`) simplesmente não têm esses campos.

O `AuditMixin`/`AuditSerializerMixin` (`apps/accounts/audit.py`, Sprint 1) foi desenhado para `models.Model` do Django ORM — `AuditMixin` é literalmente `models.Model, abstract=True`. As entidades de `decks` não são ORM (Sprint 2, D2 em `openspec/changes/sprint-2-decks-cards/design.md`: serializers manuais, sem `ModelSerializer`, porque o dado vive em MongoDB via Motor). Então o mixin do Django ORM não se aplica diretamente — precisa de um equivalente pros serializers manuais.

Da mesma forma, `Permission`/`Group` nativos geram `Permission` automaticamente (`add_<model>`, `change_<model>`, etc.) a partir de `ContentType`, que vem de migração de `models.Model` real — de novo, não existe pra `Deck`/`Card`.

## Goals / Non-Goals

**Goals:**
- `created_by`/`updated_by` reais em Deck/Card/Category/CardReview, nunca aceitos como input do cliente.
- Uma checagem de autorização além de "está autenticado" em toda view de decks/cards — hoje zero.
- Mecanismo extensível pra quando existir um segundo tipo de principal (agente de IA, Sprint 10) sem precisar redesenhar.

**Non-Goals:**
- `Permission` granular por ação (`add_deck`, `delete_card`, etc.) — não existe `ContentType` pra essas entidades sem uma gambiarra (proxy model só pra pendurar Permission). Fica pra trás enquanto só existe um tipo de usuário real (`standard_user`).
- Papéis diferenciados entre usuários humanos (admin, gerente) — o produto não tem isso; confirmado explicitamente pelo usuário (só usuário final, sem hierarquia).
- Qualquer mudança de comportamento visível pro usuário final — essa sprint é infraestrutura pura, sem UI nova.

## Decisions

### D1 — Auditoria via serializer, não via mixin de ORM
`AuditMixin` (Django `models.Model`) não se aplica a dataclasses Mongo. Em vez de forçar um mixin de ORM sobre dado não-ORM (mesmo erro que a Sprint 2 já evitou ao não usar `ModelSerializer`), `created_by`/`updated_by` são campos simples nas dataclasses de domínio (`Optional[str]`, guardando o `user.id`/email), preenchidos explicitamente em `create()`/`update()` dos serializers manuais de `apps/decks/serializers.py` — mesmo padrão que `owner_id` já usa hoje (nunca aceito do cliente, sempre de `self.context["request"].user`).

### D2 — Autorização via `Group`, não `Permission` por model
`Permission` automático depende de `ContentType`, que depende de `models.Model` migrado — não existe pra `Deck`/`Card`. Duas opções: (a) criar `Permission` manualmente presos a um `ContentType` sintético (mais granular, mais peça móvel), ou (b) usar só `Group` como rótulo grosso de capacidade, checado via `permission_classes` customizado. Escolhido (b): hoje só existe um tipo de usuário (`standard_user`, acesso total ao que é seu, via `owner_id` — não via `Permission`), então granularidade por ação seria complexidade sem consumidor real. Ainda cumpre a regra `permissoes-django` ("nativo Django, sem sistema paralelo") — só não usa a metade do framework que pressupõe ORM.
- **Alternativa descartada**: proxy `models.Model` vazio só pra ter `ContentType`/`Permission` reais. Rejeitada — adiciona uma tabela Postgres e uma migração só para satisfazer a letra da regra, sem nenhum ganho funcional hoje.

### D3 — Grupo `standard_user` atribuído automaticamente, sem grupo `ai_agent` ainda
Todo usuário (signup Google, signup e-mail/senha, seed) entra automaticamente no grupo `standard_user`. Um grupo `ai_agent` (pro Sprint 10) **não é criado agora** — YAGNI: não há consumidor real até o agente existir, e criar o grupo antes não economiza trabalho nenhum na Sprint 10 (só adicionaria uma entrada `Group.objects.create()` órfã no banco por 5 sprints).

### D4 — Autenticação service-to-service via JWT auto-assinado, não OAuth2 completo
`POST /document-generator/v1/decks/export` hoje não checa autenticação nenhuma (`grep` confirmado em `microservices/document-generator/app/routes/decks.py`), com `CORSMiddleware(allow_origins=["*"])` e a porta `8001` publicada pro host (`docker-compose.yml`) — exposição real no VPS de destino, não hipotética.

Duas famílias de solução consideradas:
- **(a) OAuth2 `client_credentials` via `django-oauth-toolkit`**: Django vira um Authorization Server (`Application`/`AccessToken` via ORM), o microsserviço chama um endpoint de token antes de cada request (ou faz introspection). Resolve delegação de acesso a clientes que não são totalmente controlados por quem opera o serviço — não é o caso aqui: hoje existe 1 client (o próprio Django), controlado pelo mesmo mantenedor dos dois lados. O "pacote pronto" só cobre o lado emissor; o lado verificador (FastAPI) precisaria ser escrito na mão de qualquer forma.
- **(b) JWT auto-assinado (HS256), verificado localmente**: Django assina um token curto (`iss` = nome do serviço chamador, `aud` = serviço de destino, `exp` curto) antes de cada chamada, em memória — sem round-trip de rede. O `document-generator` verifica assinatura + claims localmente, com o mesmo segredo compartilhado (via `.env` de cada lado). Sem Authorization Server, sem tabela de clients, sem introspection.

Escolhido (b). Motivo: o problema real é **identidade de serviço** ("qual aplicação fez essa chamada"), não delegação de acesso a terceiros — (a) resolveria um problema mais amplo do que o que existe, ao custo de infraestrutura adicional (migrations, admin, gestão de client secrets) sem benefício funcional extra hoje. (b) também elimina a necessidade de cache de autenticação: como a verificação é local, não existe chamada de rede repetida a cachear (diferente de introspection remoto, que exigiria isso).

**Segredo por par, não global**: cada par emissor↔verificador (hoje só Django↔`document-generator`) tem seu próprio segredo — um vazamento em um canal não compromete os demais quando a Sprint 10/11 adicionarem outros serviços. Chave separada do `SIMPLE_JWT`/`DJANGO_SECRET_KEY` que assina token de usuário humano, pelo mesmo motivo de blast radius.

**Rotação via `kid` versionado, não secrets manager**: o header do JWT carrega um `kid` identificando qual segredo foi usado pra assinar; o verificador mantém um mapa local `{kid: secret}` (via env var) e aceita qualquer `kid` presente nesse mapa — não só o mais recente. Rotação = adicionar a chave nova nos dois lados (redeploy), promover a nova a "ativa" no lado emissor, depois remover a antiga dos dois lados (segundo redeploy) — sem downtime, sem token rejeitado no meio da troca.
- **Alternativa descartada**: secrets manager (Vault/Doppler/AWS Secrets Manager) com TTL curto e rotação sem redeploy nenhum. Rejeitada nesse estágio — é a resposta "correta" de operação em escala, mas é infraestrutura nova rodando 24/7 num projeto solo em VPS com 2-3 microsserviços; decisão explícita do usuário (via `backend-mentor`) de que isso é overengineering aqui, revisitável se/quando a operação exigir rotação sem intervenção manual.

## Risks / Trade-offs

- **[Risco]** Se o produto algum dia precisar de papéis diferenciados entre usuários humanos (ex.: plano pago com limites diferentes), o mecanismo de `Group` único (`standard_user`) precisará crescer — mas hoje isso não é um requisito real, e o `permission_classes` já está desenhado pra checar grupo (não hardcoded pra um único grupo), então adicionar um segundo grupo humano no futuro é incremental, não uma reescrita.
- **[Risco]** `created_by`/`updated_by` como `Optional[str]` (não uma referência tipada a `User`) significa que integridade referencial não é garantida pelo schema — mas é o mesmo trade-off que `owner_id` já aceita hoje (Mongo não tem FK), consistente com o resto do domínio.
- **[Risco]** Rotação via `kid` versionado exige dois redeploys coordenados (adicionar chave nova, depois remover a antiga) — não é "zero-touch": ainda depende de alguém lembrar de fazer o segundo passo. Aceitável no estágio atual (projeto solo, rotação não é uma operação frequente); se isso passar a incomodar na prática, é o sinal concreto de que vale migrar pra um secrets manager (D4), não antes.

## Migration Plan

Sem migração de dados: campos novos em dataclasses (sem schema fixo no Mongo) começam `None`/ausentes em documentos antigos, preenchidos só em criações/edições futuras — não precisa de backfill retroativo (registros do seed já são recriados a cada `--reset`). `Group.objects.get_or_create(name="standard_user")` é idempotente, roda numa migration de dados do Django (`apps/accounts/migrations/`) ou no `AppConfig.ready()`. Segredo de serviço (JWT) é uma variável de ambiente nova em cada lado (`django/.env`, `microservices/document-generator/.env`) — sem persistência em banco, sem migração de schema.
