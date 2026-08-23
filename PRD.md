# PRD — Sistema de Flashcards Inteligente (Anki + IA)

> **Como usar este documento**: este é o guia de planejamento e execução do projeto. As regras técnicas mandatórias (o "como" e os limites invioláveis) vivem em [`PROMPT_REFINADO.md`](PROMPT_REFINADO.md) — este PRD não repete essas regras em detalhe, apenas referencia onde encontrá-las. Toda sprint aqui DEVE respeitar `<regra_obrigatoria>`, `<restricao>` e `<ponto_critico>` definidos lá. A **Sprint 0** já tem um plano de execução detalhado em `openspec/changes/migrate-to-django-microservices-architecture/tasks.md`, criado via `/opsx:propose` — quando essa sprint começar, use `/opsx:apply` para executá-la.

## 1. Visão Geral do Produto

Plataforma de flashcards inspirada no Anki, com um agente de IA que dá feedback de estudo, sugere novos cards/decks, envia lembretes via WhatsApp e gera relatórios periódicos de desempenho em PDF. Projeto pessoal com objetivo duplo: entregar um produto funcional e servir de veículo de aprendizado guiado (system design, Terraform/AWS, Kubernetes) via mentoria.

## 2. Funcionalidades Obrigatórias

Fonte de verdade: `<funcionalidades_obrigatorias>` em `PROMPT_REFINADO.md`.

| ID | Funcionalidade | Resumo |
|---|---|---|
| `flashcards-core` | Flashcards core | Deck → categoria → card, repetição espaçada |
| `feedback-ia` | Agente de IA | Analisa desempenho, dá feedback diário, sugere cards/decks |
| `notificacao-whatsapp` | Lembretes WhatsApp | Via Evolution API, respeitando meta de estudo |
| `relatorio-semanal-email` | Relatório semanal PDF | Por e-mail, com estatísticas + resumo de evolução |
| `home-dashboard` | Home | Último deck, meta/%, feedback do dia, gráfico (exportável a PDF) |
| `exportacao-anki` | Exportação Anki | `.apkg` compatível com o Anki real |

## 3. Arquitetura Técnica (resumo)

Fonte de verdade completa: `<stack_tecnologica>` e `<arquitetura>` em `PROMPT_REFINADO.md`. Resumo:

- **Backend principal**: Django + DRF (`django/core` + `django/apps/`), multi-tenant, URLs versionadas, PostgreSQL para `auth`/`Permission`/`Group`.
- **Persistência de domínio**: MongoDB (deck/card/estatísticas).
- **Microsserviços FastAPI** (MVC), em `microservices/<nome>/`: geração de documentos/exportação Anki → agente de IA (LangChain/LangGraph) → WhatsApp (Evolution API) — nessa ordem.
- **Estrutura do monorepo**: `django/` (backend principal), `microservices/<nome>/` (um por serviço), `frontend/` (SPA React) — cada unidade implantável em sua própria pasta na raiz; `docker-compose.yml`/`Makefile` orquestram todas elas a partir da raiz.
- **Assincronismo**: Celery + RabbitMQ (broker) + Redis (result backend/cache) — nada bloqueia o ciclo request/response.
- **Frontend**: SPA React, build estático hospedado em AWS S3.
- **Gráficos**: client-side no React, sem microsserviço dedicado.
- **Deploy real**: VPS Hostinger, Docker Compose (não Kubernetes, não Terraform/AWS — ver seção 10).
- **Observabilidade**: logs estruturados → Prometheus/Grafana → node_exporter → exporter RabbitMQ/Celery.
- **Design**: `design_system/design-system.html` é a fonte única de verdade visual.

## 4. Requisitos Não-Funcionais

- **Responsividade**: sistema funcional em qualquer tamanho de tela.
- **Segurança**: isolamento multi-tenant rigoroso, permissões de arquivos/mídia, sem dados sensíveis expostos.
- **UI/UX**: aderência estrita ao design system, bom contraste, jornadas fluidas.
- **UX de tarefas assíncronas**: loading no botão + aviso "você será notificado" + notificação in-app ao concluir — nunca bloqueante.
- **Performance**: filtros/telas/processos rápidos, meta de escala de design = 10k usuários ativos (ver `<escala>`).
- **Demonstração**: `management command` de seed com dados fake cobrindo múltiplos cenários/usuários/datas.

## 5. Critérios de Aceite Globais

Lista completa em `<criterios_de_aceite>` de `PROMPT_REFINADO.md` (12 itens) — cada sprint abaixo referencia quais critérios ela ajuda a satisfazer.

## 6. Decisões de Arquitetura Já Tomadas

Todas em `<decisoes_resolvidas>` de `PROMPT_REFINADO.md`. Resumo rápido:

| Decisão | Resultado |
|---|---|
| Fila | RabbitMQ |
| VPS | Hostinger (confirmar preço de renovação) |
| Orquestração | Docker Compose (Kubernetes é trilha de estudo separada) |
| Banco relacional Django | PostgreSQL (containerizado local e prod) |
| Stack de gráficos | Client-side React |
| Hospedagem frontend | AWS S3 |
| Deploy real | VPS (não AWS) |
| Terraform/AWS | Trilha de estudo separada, desacoplada |
| Domínio | Cloudflare (registrador), sem pressa |
| Rate limiting | 3 req/s |
| Meta de escala | 10k usuários ativos (design, não infra) |
| Observabilidade | logs → métricas → host → fila/DLQ |
| Ordem microsserviços | Documentos → IA → WhatsApp |

Únicas pendências reais: dashboards/alertas do Grafana (detalhamento fino, via `backend-mentor` na Sprint 14) e o mapeamento de idempotência (`<ponto_critico id="idempotencia-revisao">`, Sprint 15).

---

## 7. Roadmap de Sprints

> **Convenção de testes**: a partir da Sprint 1, toda sprint inclui uma tarefa final de testes automatizados (pytest/pytest-django no Django, pytest+httpx nos microsserviços FastAPI), escrita depois que as tarefas de feature da sprint estiverem implementadas — não TDD, testes ao final de cada leva de tarefas executadas. A Sprint 0 (fundação) ficou intencionalmente sem essa infraestrutura.

### Sprint 0 — Fundação de Arquitetura (Django + Domínio + Ambiente Local)

**Objetivo**: sair do monólito FastAPI incompleto atual para o esqueleto da arquitetura-alvo, sem nenhuma feature de produto ainda. **Plano de execução detalhado** em `openspec/changes/migrate-to-django-microservices-architecture/tasks.md` (8 grupos, ~40 tarefas), executado via `/opsx:apply`. **Concluída** — ver `CHANGELOG.md`.

- [x] 0.1 Criar projeto Django (`core` + `apps/`, dentro de `django/`), PostgreSQL para auth, settings segregados por ambiente
- [x] 0.2 Consolidar domínio reaproveitável de `legacy/` (entities Card/Deck/GenerationSession, repositórios Mongo) em `django/apps/decks/`
- [x] 0.3 `docker-compose.yml` na raiz: Django, Postgres, MongoDB, Redis, RabbitMQ, non-root, entrypoint
- [x] 0.4 Corrigir `Makefile` e unificar `pyproject.toml`/`requirements.txt`
- [x] 0.5 Reclassificar o FastAPI atual como microsserviço de documentos (`microservices/document-generator/`)
- [x] 0.6 Remover `legacy/` após migração validada
- [x] 0.7 Atualizar changelog
- [x] 0.8 Reorganizar a raiz do monorepo: `django/` (backend principal), `microservices/<nome>/` (um por microsserviço), `frontend/` (placeholder da Sprint 3) — cada unidade implantável como pasta própria, `docker-compose.yml`/`Makefile` continuam na raiz

*Critérios de aceite relevantes: 8, 10.*

---

### Sprint 1 — Autenticação & Multi-tenant

**Objetivo**: base de segurança sobre a qual todo o resto é construído — nada de feature de produto avança sem isso. **Concluída** — ver `openspec/changes/sprint-1-autenticacao-multi-tenant/` e `CHANGELOG.md`.

- [x] 1.1 Model de usuário reaproveitando o nativo do Django + `email` como campo único (`django/apps/accounts/models.py`)
- [x] 1.2 Autenticação via Google (OAuth) — `django-allauth` + `dj-rest-auth` + `simplejwt`; ⚠️ requer `GOOGLE_OAUTH_CLIENT_ID`/`SECRET` reais (Google Cloud Console) para o fluxo completo funcionar de ponta a ponta — ainda não configurado
- [x] 1.3 Lógica de permissões sobre `Permission`/`Group` nativos do Django (sem sistema paralelo) — validado com o `User` customizado
- [x] 1.4 Mixin/base de queryset que filtra por tenant em toda query (`TenantOwnedModel`/`TenantOwnedQuerySet`) — testado explicitamente contra acesso cross-tenant
- [x] 1.5 Model/mixin de auditoria (`created_at/by`, `updated_at/by`), preenchido automaticamente pelos serializers a partir da request (`AuditMixin`/`AuditSerializerMixin`)
- [x] 1.6 Implementar rate limiting (3 req/s por usuário/cliente) — throttle classes do DRF, validado com burst real (3 OK, 4ª+ recebem 429)
- [x] 1.7 Cache do token de autenticação (evitar reautenticação enquanto válido) — refresh token com blocklist no Redis, revogação testada de ponta a ponta
- [x] 1.8 Configurar pytest + pytest-django (primeira infraestrutura de testes automatizados do projeto)
- [x] 1.9 Testes automatizados cobrindo as tarefas 1.1–1.7 (12 testes, todos passando)

*Critérios de aceite relevantes: 1.*

---

### Sprint 2 — Decks & Cards (domínio core)

**Objetivo**: a funcionalidade central do produto — sem isso, nada mais tem dado real para trabalhar em cima.

- [x] 2.1 Endpoints versionados (`/api/v1/`) de CRUD para decks, categorias e cards (Generic Views do DRF) — `apps/decks/views.py`/`urls.py`; `Category` é entidade nova (não existia no domínio migrado)
- [x] 2.2 Lógica de repetição espaçada como base do fluxo de estudo — FSRS via pacote `fsrs` (`domain/services/scheduling_service.py`), não SM-2 manual
- [x] 2.3 Registro de sessões de estudo (acertos/erros, timestamps) para alimentar estatísticas futuras — entidade `CardReview` (um evento por revisão, não uma "sessão" agregada — mesma granularidade do `revlog` do Anki; deliberadamente distinta de `GenerationSession`). **Ajustado na Sprint 3**: `CardReview` ganhou `deck_id` denormalizado a partir de `Card.deck_id` no momento da revisão — referência estável (nunca muda), diferente de denormalizar um título/nome, então sem risco de ficar desatualizado.
- [x] 2.4 Índices obrigatórios: deck, categoria, tag de relacionamento deck/card — `IndexDefinitions` em `schemas.py`, agora fonte única também para `MongoDBConnectionManager.create_indexes()`
- [x] 2.5 Serializers magros, herdáveis, sem boilerplate desnecessário — `serializers.Serializer` manuais (não `ModelSerializer`, que exige Model Django real)
- [x] 2.6 Django management command de seed: múltiplos usuários/tenants, decks/categorias variadas, cards com históricos de acerto/erro, datas passadas/recentes/futuras — protegido contra execução em produção, idempotente ou com `--reset` — `seed_decks` (validado rodando de verdade contra Mongo/Postgres reais). **Ajustado na Sprint 3**: títulos/descrições de deck passaram de um padrão genérico (`"Categoria — Deck N"`, `description` sempre vazia) para conteúdo real e variado (`DECK_CATALOG` em `seed_decks.py`) — gap encontrado testando a Home de verdade, onde o título genérico não servia como identificador amigável.
- [x] 2.7 Testar comando de seed e a proteção contra produção explicitamente — `test_seed_command.py`; **28/28 testes passando** (Sprint 1 + 2)

**Nota de implementação**: isolamento multi-tenant em MongoDB precisou de mecanismo próprio (não o `TenantOwnedModel` da Sprint 1, que é ORM/Postgres-only) — `owner_id` obrigatório em toda assinatura de método de repositório. Um bug real de produção foi descoberto e corrigido durante a verificação end-to-end via HTTP: `AsyncIOMotorClient` ficava preso ao event loop em que era criado, e `async_to_sync` cria um loop novo a cada chamada — quebrava a partir da segunda/terceira chamada bridged do processo (ver Risks em `openspec/changes/sprint-2-decks-cards/design.md`).

*Critérios de aceite relevantes: 11.*

---

### Sprint 3 — Frontend Base & Home Dashboard

**Objetivo**: primeira superfície visual real do sistema, consumindo a API já funcional.

- [x] 3.1 Scaffold da SPA React + pipeline de build — Vite, `frontend/`
- [x] 3.2 Consultar `design_system/design-system.html` e extrair os tokens antes de implementar qualquer tela — `design-system.html` documenta `refs/Ashley_files/style.css` (template de portfólio, não design system de app); tokens extraídos por auditoria real (`frontend/src/tokens/AUDIT.md`), não importados diretamente
- [x] 3.3 Home: último deck estudado, meta de estudo + % alcançado, gráfico de estatísticas (client-side, consumindo API do Django) — meta de estudo é client-side (localStorage), sem endpoint de backend (não existia esse conceito); gráfico via Chart.js consumindo `GET /api/v1/reviews/` (endpoint novo, gap encontrado em implementação — Sprint 2 persistia `CardReview` sem expor leitura). **Segundo gap encontrado testando a Home**: `Deck.title` gerado pelo seed era um padrão genérico (`"Categoria — Deck N"`), sem servir como identificador amigável — corrigido no seed (ver nota na tarefa 2.6) e a Home agora também exibe `Deck.description` (campo já existente desde a Sprint 2, nunca populado) quando presente.
- [x] 3.4 Exportação do gráfico da home para PDF — `jsPDF`, direto do canvas do Chart.js
- [x] 3.5 Menu lateral: decks, categorias, geração de relatórios, chat com agente de IA (placeholder até Sprint 10) — `react-router`, chat IA sem nenhuma chamada de API; botão de recolher/expandir e "Sair" (logout) adicionados
- [x] 3.6 Auditoria de consistência visual contra o design system — `frontend/src/tokens/VISUAL_AUDIT.md`, 2 desvios encontrados e corrigidos
- [x] 3.7 Tela de login (Google OAuth + e-mail/senha) — gap encontrado testando a Sprint 3: não havia nenhum plano, em nenhuma sprint futura, para sair do fluxo manual de token colado no `localStorage`. `/login` (`LoginPage.jsx`) tem dois fluxos: Google OAuth2 "token client" do Google Identity Services (`access_token`, não o ID token do botão "Sign In" mais novo — incompatível com o `GoogleOAuth2Adapter` do backend), que depende de `GOOGLE_OAUTH_CLIENT_ID`/`SECRET` reais (Google Cloud Console) para validação ponta a ponta e por enquanto fica "implementado, validação real pendente"; e login por e-mail/senha (`dj_rest_auth.views.LoginView`, novo em `apps/accounts/urls.py`), **já validado ponta a ponta via seed** — exigiu duas correções de config do allauth (`ACCOUNT_LOGIN_METHODS`/`ACCOUNT_SIGNUP_FIELDS`, ver CHANGELOG) e um fix no comando de seed (senha `anki12345` agora é setada incondicionalmente em todo usuário seedado, antes ficava "usável" mas em branco em reruns). Cadastro de conta nova e vínculo de conta pelo mesmo e-mail continuam fora de escopo — ver 7.1
- [x] 3.8 Fluxo de refresh de token no frontend + tratamento explícito de 401 (sessão expirada) — gap encontrado testando a Sprint 3: a SPA nunca guardava o refresh token nem tinha uma resposta clara a um access token expirado. `apiFetch` agora detecta 401, tenta `/auth/token/refresh/` automaticamente (com deduplicação de chamadas concorrentes) e repete a chamada original; se o refresh também falhar, dispara `auth:session-expired` (`AuthContext` redireciona pra `/login`)

*Critérios de aceite relevantes: 12.*

**Nota de implementação**: `GET /api/v1/reviews/` foi adicionado durante a Sprint 3 (não estava no escopo original, que previa "nenhum impacto no backend") — a Sprint 2 persistia `CardReview` mas nunca expunha leitura via API; a Home precisava desse histórico. Impacto mínimo: um método de repositório (`find_by_owner`) + uma Generic View, reaproveitando o padrão já estabelecido.

---

### Sprint 4 — Robustecimento do Frontend

**Objetivo**: fecha pontas reais da Sprint 3, encontradas via `backend-mentor` (grep no código, não suposição): zero responsividade (`grep "@media"` não encontra nada, apesar de ser `<regra_obrigatoria>` em `PROMPT_REFINADO.md`), sem error boundary (uma exceção JS derruba a tela pra branco sem recuperação), inconsistência de estilo (`LoginPage.jsx`/`HomePage.jsx` usam inline `style`, os outros 6 componentes usam CSS dedicado com tokens), bundle sem code-splitting, sem favicon (`index.html` não tem `<link rel="icon">`) e sem testes automatizados de frontend. Inserida antes da Sprint 5 (Fundações Transversais) de propósito — as próximas sprints adicionam bastante UI nova (formulários, dropdown), e construir isso sobre um frontend inconsistente e sem proteção mínima só reproduziria o problema em vez de corrigi-lo.

- [x] 4.1 Code-splitting: `import()` dinâmico de `jsPDF`+`html2canvas`, carregados só ao clicar "Exportar PDF" — build validado com chunks separados (`jspdf` 391 kB, `html2canvas` 202 kB e principal 338 kB, tamanhos não comprimidos)
- [x] 4.2 `LoginPage.jsx`/`HomePage.jsx` migrados de inline `style` pra CSS dedicado com tokens, no mesmo padrão de `Sidebar`/`Card`/`Button`/`Input`/`AppShell`
- [x] 4.3 Error boundary global em `App.jsx`, com tela de fallback simples em vez de branco
- [x] 4.4 Responsividade: breakpoint tablet (1024px) — sidebar colapsa automaticamente (reaproveita o toggle já existente da Sprint 3), grid da Home e formulários com `max-width`, sem quebra horizontal. Mobile de verdade (nav diferente) fica fora de escopo por decisão explícita — projeto pessoal, sem uso mobile previsto no curto prazo
- [x] 4.5 Favicon PNG derivado do mascote exibido no `README.md`, otimizado para 192×192 e referenciado em `index.html`
- [x] 4.6 Validação em Chrome headless a 1024×768 — Login e Home inspecionadas; Home com sidebar colapsada e `scrollWidth === viewportWidth === 1024`, sem quebra horizontal
- [x] 4.7 Fundação mínima de testes frontend — Vitest + React Testing Library + jsdom, scripts `test`/`test:watch` e setup compartilhado; 6 testes cobrem fallback do error boundary, auto-colapso/reação ao viewport, precedência da preferência manual persistida e carregamento sob demanda da exportação PDF

*Critérios de aceite relevantes: 12 (consistência visual) — responsividade é `<regra_obrigatoria>` nos Requisitos Não-Funcionais (seção 4 do PRD), mas não tem item próprio na lista de 12 critérios de aceite.*

---

### Sprint 5 — Fundações Transversais: Auditoria & Permissões

**Objetivo**: auditoria via `backend-mentor` encontrou que regras mandatórias declaradas em `PROMPT_REFINADO.md` desde a Sprint 0/1 (`permissoes-django`, `auditoria`) nunca foram de fato aplicadas — `DEFAULT_PERMISSION_CLASSES` é só `IsAuthenticated` em toda view, e `Deck`/`Card`/`Category`/`CardReview` não têm `created_by`/`updated_by` (o `AuditMixin` da Sprint 1 só existe no app `accounts`, nunca usado pelas entidades de produto). Fechar isso agora, enquanto a superfície (poucos endpoints) torna o retrofit barato — a Sprint 10 (Agente de IA) já exige `created_by`/`updated_by = "ai_agent_machine"`, campo que hoje nem existe. Escopo ampliado via `backend-mentor` pra também endurecer a autenticação **service-to-service** (Django→microsserviço), movida pra cá da Sprint 9: hoje `document-generator` está com o endpoint de export sem autenticação nenhuma e a porta publicada pro host — ver `autenticacao-service-to-service-jwt`.

- [ ] 5.1 `created_by`/`updated_by` em `Deck`, `Card`, `Category`, `CardReview` — preenchidos automaticamente pelos serializers a partir da request autenticada, nunca aceitos como input do cliente (mesmo princípio do `AuditSerializerMixin` da Sprint 1, adaptado aos serializers manuais do domínio Mongo, já que essas entidades não são `models.Model`)
- [ ] 5.2 Grupo `standard_user` (Django `Group` nativo) atribuído automaticamente a todo usuário no signup e no seed — `Permission` por model não se aplica aqui (`Deck`/`Card` não têm `ContentType`, por não serem `models.Model`); a checagem é por grupo, não por `Permission` granular
- [ ] 5.3 `permission_classes` customizado verificando pertencimento ao grupo, substituindo o `IsAuthenticated` puro nas views de decks/cards/categories/reviews — mecanismo pensado pra aceitar um grupo `ai_agent` na Sprint 10 sem mudar de estrutura
- [ ] 5.4 JWT de serviço (HS256) auto-assinado pelo Django em toda chamada ao `document-generator` — segredo compartilhado só entre esse par (não global), verificação local no FastAPI (sem introspection/round-trip), claim `iss` identificando a aplicação chamadora, expiração curta (30-60s), chave de assinatura separada do `SIMPLE_JWT`/`DJANGO_SECRET_KEY` de usuário
- [ ] 5.5 Rotação de chave de serviço via `kid` versionado no header do JWT — verificador aceita qualquer `kid` presente no seu mapa local de segredos, permitindo rotação sem downtime em dois redeploys (chave nova aceita → promovida a ativa → chave antiga removida)
- [ ] 5.6 Testes automatizados: audit fields preenchidos corretamente em create/update, protegidos contra input do cliente, grupo atribuído automaticamente a todo novo usuário, acesso negado fora do grupo, chamada ao `document-generator` rejeitada sem JWT de serviço válido (assinatura errada, expirado, `kid` desconhecido)

*Critérios de aceite relevantes: 1 (isolamento multi-tenant).*

---

### Sprint 6 — Ciclo de Vida de Deck/Card

**Objetivo**: hoje só existe create/read completo — falta edição real de Deck/Card, exclusão com retenção (soft delete, não delete físico direto) e uma meta de estudo por deck persistida no backend (substitui o "meta de estudo" client-side provisório da Sprint 3, decisão `meta-de-estudo-client-side`). Depende da Sprint 5 (audit fields/permissões) já estar pronta. Decisões fechadas via `backend-mentor`: soft delete por timestamp (não booleano), sem relação N:N entre Card e Deck (mantém 1 card = 1 deck), meta por deck alimenta a Sprint 7.

- [ ] 6.1 `deleted_at: Optional[datetime]` em `Deck` e `Card` — soft delete por timestamp, permite calcular a janela de 7 dias diretamente (não um booleano)
- [ ] 6.2 Todo método de repositório existente (`find_by_owner`, `find_by_deck_id`, busca de cards devidos do FSRS, a agregação da Sprint 7, etc.) passa a filtrar `deleted_at: None` por padrão, via um helper único de query — não repetido manualmente em cada método
- [ ] 6.3 `DELETE /api/v1/decks/{deck_id}/` faz cascade: marca `deleted_at` em todos os cards do deck junto — sem caso de "desvincular", porque não existe relação N:N (card sempre pertence a exatamente um deck)
- [ ] 6.4 `DELETE /api/v1/cards/{card_id}/` — soft delete individual de card
- [ ] 6.5 Task Celery Beat diária que purga permanentemente (delete físico) registros com `deleted_at` há mais de 7 dias — primeira task Celery real do projeto (Celery Beat instalado desde a Sprint 0, nunca usado até aqui)
- [ ] 6.6 `daily_review_goal: Optional[int]` em `Deck`, editável via `PATCH` — meta de cards a revisar daquele deck, substituindo o "meta de estudo" client-side da Sprint 3
- [ ] 6.7 Edição completa de `Deck` (nome, categoria, `daily_review_goal`) e `Card` (conteúdo, tags) via `PATCH` — endpoints já existem como Generic Views, completar os campos editáveis
- [ ] 6.8 Tratamento de `403` na SPA — `apiFetch` hoje só trata `401`; a partir da Sprint 5 (permissão por grupo) um `403` real pode acontecer, e a UI precisa de uma mensagem distinta ("sem permissão"), não o erro genérico
- [ ] 6.9 Testes automatizados: soft delete filtra corretamente em toda query existente, cascade Deck→Card funciona, purge remove após 7 dias e preserva antes disso, `daily_review_goal` editável

*Critérios de aceite relevantes: 1 (isolamento continua íntegro com soft delete).*

---

### Sprint 7 — Estatísticas por Deck

**Objetivo**: gap encontrado testando a Home da Sprint 3 — o gráfico de estatísticas mistura todos os decks do usuário, sem forma de filtrar por um deck específico, e "cards revisados hoje" é calculado inteiro no cliente a partir de `GET /api/v1/reviews/`, o que não escala. Decisões já fechadas em `PROMPT_REFINADO.md` (`estatisticas-por-deck-endpoint`, `dropdown-deck-home`, `cards-revisados-hoje-sem-campo-novo`). **Depende da Sprint 6**: a agregação precisa excluir registros com `deleted_at` (soft delete) e a resposta passa a incluir progresso contra `daily_review_goal`, ambos campos que só existem a partir dali.

- [ ] 7.1 `GET /api/v1/decks/{deck_id}/statistics/` — distribuição de revisões por rating (again/hard/good/easy), quantidade revisada hoje e progresso contra `daily_review_goal`, tudo escopado a `deck_id` e `owner_id`, excluindo cards/decks com `deleted_at` preenchido; calculado via agregação Mongo (`$match`/`$group`), não trazendo os documentos crus pra API e somando em Python
- [ ] 7.2 Dropdown na Home, acima do gráfico de Estatísticas, listando os decks do usuário (`GET /api/v1/decks/`) e disparando o novo endpoint ao selecionar
- [ ] 7.3 Sem seleção manual no dropdown, o deck exibido (card + gráfico) é o mais recentemente estudado — mesmo comportamento hoje existente em "Último deck estudado", reaproveitado como default
- [ ] 7.4 Título do card muda de "Último deck estudado" para "Deck estudado" quando o usuário seleciona manualmente um deck no dropdown (deixa de ser necessariamente o mais recente)
- [ ] 7.5 Separação visual entre o grid superior (último deck estudado/meta de estudo) e o card de Estatísticas — padding entre as bordas, bordas mais grossas
- [ ] 7.6 Testes automatizados (pytest) cobrindo a agregação/endpoint de estatísticas por deck, incluindo isolamento multi-tenant e exclusão de registros soft-deletados

*Critérios de aceite relevantes: 1 (isolamento multi-tenant), 12 (consistência visual).*

---

### Sprint 8 — Testes & CI/CD

**Objetivo**: ampliar a fundação mínima de testes frontend criada na Sprint 4 para uma cobertura abrangente dos dois lados (backend já tem pytest desde a Sprint 1) + pipeline de integração contínua no GitHub Actions, rodando ambos antes de qualquer merge. Inserida aqui de propósito — depois que as Sprints 4–7 consolidam novos comportamentos, antes das integrações externas das sprints seguintes.

- [ ] 8.1 Evoluir a configuração de Vitest + React Testing Library iniciada na Sprint 4 — adicionar relatório de cobertura, limites mínimos e utilitários compartilhados necessários para a suíte abrangente
- [ ] 8.2 Testes automatizados para a camada de API client (`apiFetch`, refresh de token, tratamento de 401/403) e hooks (`useApiResource`, `useLastStudiedDeck`)
- [ ] 8.3 Testes automatizados para os componentes/telas críticos (Home, login, navegação)
- [ ] 8.4 Pipeline GitHub Actions — job de backend: `pytest` com Postgres/MongoDB/Redis como service containers, rodando em cada PR
- [ ] 8.5 Pipeline GitHub Actions — job de frontend: lint + testes + build, rodando em cada PR
- [ ] 8.6 Badge de status do CI no `README.md`

*Critérios de aceite relevantes: 8 (lint/PEP-8 já cobre backend; aqui vira gate automatizado de CI, não só `pre-commit` local).*

---

### Sprint 9 — Exportação Anki & Microsserviço de Documentos

**Objetivo**: fechar o ciclo do microsserviço de documentos já reclassificado na Sprint 0, ligando-o de ponta a ponta. Autenticação service-to-service já resolvida na Sprint 5 (`autenticacao-service-to-service-jwt`) — esta sprint só consome o JWT de serviço já implementado, não define o mecanismo.

- [ ] 9.1 Endpoint Django que dispara (via Celery) a geração de `.apkg` no microsserviço de documentos, autenticando a chamada com o JWT de serviço da Sprint 5
- [ ] 9.2 Circuit breaker + retry exponencial na chamada Django → microsserviço de documentos
- [ ] 9.3 Contrato de payload/resposta documentado entre Django e o microsserviço, incluindo o header de autenticação
- [ ] 9.4 Geração de PDF genérica no mesmo microsserviço (reaproveitada na Sprint 12)
- [ ] 9.5 Validar `.apkg` gerado abrindo no Anki real

*Critérios de aceite relevantes: 2, 7, 9.*

---

### Sprint 10 — Agente de IA (LangChain/LangGraph)

**Objetivo**: a funcionalidade de maior risco/novidade técnica — só começa depois que decks/cards (Sprint 2) está sólido.

- [ ] 10.1 Microsserviço FastAPI do agente (LangChain/LangGraph), padrão MVC
- [ ] 10.2 Restrição de domínio fechado: só cards/decks/feedback de estudo — recusar qualquer pedido fora disso (ver `<escopo_agente_ia>`)
- [ ] 10.3 Limite rígido de 100 caracteres por card gerado, com descarte automático acima disso
- [ ] 10.4 Toda ação do agente passa pelas rotas de API existentes, autenticada com o grupo `ai_agent` (ver `permissoes-django`, Sprint 5) — nunca acesso direto ao banco
- [ ] 10.5 `created_by`/`updated_by` = `"ai_agent_machine"` em todo recurso criado pelo agente
- [ ] 10.6 Defesas contra prompt injection (redefinição de papel, extração de dados de outros tenants)
- [ ] 10.7 Feedback diário na home + sugestão de novos cards/decks, sempre assíncrono via Celery
- [ ] 10.8 Testes cobrindo os exemplos adequado/inadequado/uso indevido já definidos em `<exemplos_de_uso>`

*Critérios de aceite relevantes: 2, 3, 4, 5.*

---

### Sprint 11 — Notificações WhatsApp (Evolution API)

**Objetivo**: último microsserviço da ordem definida — mais desacoplado do resto, entra por último de propósito.

- [ ] 11.1 Microsserviço FastAPI de integração com a Evolution API, padrão MVC
- [ ] 11.2 Envio de lembrete de estudo respeitando a meta de tempo definida pelo usuário
- [ ] 11.3 Disparo assíncrono via Celery (Celery Beat para agendamento periódico)
- [ ] 11.4 Circuit breaker + retry + DLQ na comunicação com a Evolution API

*Critérios de aceite relevantes: 2, 9.*

---

### Sprint 12 — Relatório Semanal por E-mail

**Objetivo**: fecha o loop de feedback do produto, reaproveitando o gerador de documentos (Sprint 9) e as estatísticas (Sprint 2/Sprint 7).

- [ ] 12.1 Task Celery Beat semanal que coleta estatísticas de estudo do período
- [ ] 12.2 Geração do PDF do relatório via microsserviço de documentos
- [ ] 12.3 Resumo textual de evolução (pode reaproveitar o agente de IA da Sprint 10, dentro do escopo permitido)
- [ ] 12.4 Envio automático por e-mail, sem intervenção manual

*Critérios de aceite relevantes: 2, 6.*

---

### Sprint 13 — Deploy Real (VPS + S3 + Domínio)

**Objetivo**: tirar o sistema do "só roda local" e colocá-lo no ar de verdade.

- [ ] 13.1 `docker-compose.yml` de produção + processo de deploy (SSH + compose) na VPS Hostinger
- [ ] 13.2 Bucket S3 de hospedagem estática do frontend + pipeline de build/upload (GitHub Actions — reaproveita o job de frontend da Sprint 8)
- [ ] 13.3 Compra do domínio via Cloudflare (sem pressa — só quando o usuário decidir) + configuração de DNS
- [ ] 13.4 Fluxo de deploy baseado em tags via GitHub Actions
- [ ] 13.5 Confirmar preço de renovação da Hostinger antes de qualquer contratação anual

*Critérios de aceite relevantes: 10.*

---

### Sprint 14 — Observabilidade

**Objetivo**: visibilidade operacional do sistema real em produção.

- [ ] 14.1 Logs estruturados JSON com `request_id` propagado, no Django e nos microsserviços
- [ ] 14.2 `django-prometheus` no Django + instrumentação equivalente em cada FastAPI
- [ ] 14.3 `node_exporter` na VPS
- [ ] 14.4 Exporter de RabbitMQ/Celery, com foco em profundidade de fila e de DLQ
- [ ] 14.5 **Mentoria via `backend-mentor`**: decidir quais dashboards Grafana montar primeiro e a política de alertas (decisão ainda pendente — `dashboards-alertas-grafana`)
- [ ] 14.6 Montar os dashboards e alertas decididos na 14.5

*Critérios de aceite relevantes: nenhum específico, mas suporta a operação de todos os demais.*

---

### Sprint 15 — Hardening & Revisão Final

**Objetivo**: fechar as pontas soltas que só fazem sentido revisar com o sistema inteiro construído.

- [ ] 15.1 Mapear quais operações precisam de garantia de idempotência (consumers de fila, tasks Celery, WhatsApp, geração de PDF) — resolve `<ponto_critico id="idempotencia-revisao">`
- [ ] 15.2 Implementar as proteções de idempotência mapeadas em 15.1
- [ ] 15.3 Auditoria final de isolamento multi-tenant em toda query/serializer/endpoint — inclui resolver os pontos ainda abertos em "Pontos de Refinamento Futuro" (seção 7.1)
- [ ] 15.4 Testar circuit breaker + retry exponencial simulando indisponibilidade de cada microsserviço
- [ ] 15.5 Checklist final contra os 12 itens de `<criterios_de_aceite>`
- [ ] 15.6 Revisão de segurança: permissões de arquivos/mídia, segredos fora do código-fonte

---

## 7.1 Pontos de Refinamento Futuro

Gaps reais encontrados durante a implementação, deliberadamente adiados — não bloqueiam a sprint em que foram descobertos, mas precisam ser resolvidos antes do sistema ser considerado "pronto" (ver Sprint 15, tarefa 15.3). Cada item cita a sprint/contexto onde foi encontrado.

**Regra de processo**: sempre que uma nova sprint estiver prestes a começar, o modelo DEVE relembrar o usuário dos itens ainda em aberto nesta seção antes de iniciar o trabalho — não silenciosamente ignorar nem assumir que já foram resolvidos.

**Nota**: login por e-mail/senha em si já está resolvido (ver tarefa 3.7) — os itens abaixo sobre e-mail/vínculo de conta são sobre **cadastro de conta nova** e **vínculo entre Google e senha no mesmo e-mail**, não sobre login de usuário já existente.

- [x] ~~Cascade delete de `CardReview`~~ **Resolvido na Sprint 6** (encontrado na Sprint 3): decidido via `backend-mentor` — soft delete cascateia de `Deck` pra `Card` (`deleted_at` em ambos), `CardReview` nunca é apagada (mantida como histórico "congelado"), só passa a ser excluída das estatísticas (Sprint 7) quando o `card_id`/`deck_id` associado está soft ou permanentemente deletado.
- [ ] **`EMAIL_BACKEND`/SMTP não configurado em lugar nenhum** (encontrado na Sprint 3, ao levantar requisitos de login por e-mail/senha): nem verificação de e-mail, nem "esqueci minha senha" funcionam sem isso. Hoje só é requisito explícito na Sprint 12 (Relatório Semanal por E-mail) — decidir se adianta pra quando o cadastro por e-mail/senha for implementado, ou se esses fluxos ficam bloqueados até lá.
- [ ] **Vínculo de conta quando Google e e-mail/senha usam o mesmo e-mail** (encontrado na Sprint 3): decidir entre vínculo automático sem verificação (simples, risco de sequestro de conta), vínculo automático só com e-mail verificado (mais seguro, depende do item de e-mail acima), ou nenhum vínculo automático (contas separadas ou colisão recusada). Ver levantamento de requisitos completo na conversa da Sprint 3.
- [ ] **`ACCOUNT_EMAIL_VERIFICATION`: `"none"` vs `"mandatory"`** (encontrado na Sprint 3): hoje desligado (`"none"`). Ativar depende do item de e-mail acima e trava a decisão de vínculo de conta.
- [ ] **Fluxo de "esqueci minha senha"** (encontrado na Sprint 3): endpoints prontos no `dj-rest-auth`, mas dependem de e-mail configurado (mesmo bloqueador acima) — decidir se entra junto com o login por e-mail/senha ou fica pra depois.

---

## 8. Trilhas de Aprendizado Paralelas (fora do roadmap principal)

Não bloqueiam nenhuma sprint acima — conduzidas via `backend-mentor` quando o usuário decidir retomar cada assunto:

- [ ] **Terraform + AWS**: projeto de estudo isolado, começando pelo state backend (S3 + DynamoDB) e um compute mínimo free-tier.
- [ ] **Kubernetes**: primeiro contato do usuário com a ferramenta — começar por `kind`/`minikube` local antes de qualquer cluster com IP público. (Ver memória: usuário pediu para retomar esse assunto mais tarde.)

---

## 9. Ordem de Execução

```
Sprint 0 (fundação) → Sprint 1 (auth/multi-tenant) → Sprint 2 (decks/cards)
   → Sprint 3 (frontend/home) → Sprint 4 (robustecimento do frontend)
   → Sprint 5 (fundações transversais: auditoria & permissões)
   → Sprint 6 (ciclo de vida de deck/card) → Sprint 7 (estatísticas por deck)
   → Sprint 8 (testes & CI/CD) → Sprint 9 (exportação Anki/documentos)
   → Sprint 10 (IA) → Sprint 11 (WhatsApp) → Sprint 12 (relatório semanal)
   → Sprint 13 (deploy real) → Sprint 14 (observabilidade) → Sprint 15 (hardening)
```

Esta ordem segue `<instrucoes_de_execucao>` item 3 de `PROMPT_REFINADO.md` e a ordem de microsserviços já decidida (`ordem-microservicos`). Cada sprint DEVE ser entregue e validada antes de avançar para a próxima — nunca pular etapas de segurança em nome de velocidade. As Sprints 4-8 foram inseridas fora da ordem original — decisão do usuário, todas via `backend-mentor`: 4 fecha pontas reais da Sprint 3 (responsividade zero, sem error boundary, inconsistência de estilo, bundle sem code-splitting, sem favicon) antes que mais UI se acumule sobre esse frontend; 5 e 6 vieram de uma auditoria que achou regras mandatórias (`permissoes-django`, `auditoria`) declaradas desde a Sprint 0/1 mas nunca implementadas, e um ciclo de vida de Deck/Card incompleto (sem edição real, sem exclusão com retenção); 7 é um gap encontrado testando a Home da Sprint 3; 8, para não deixar o frontend crescer sem cobertura de teste nem pipeline de CI.
