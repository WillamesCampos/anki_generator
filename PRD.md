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

Únicas pendências reais: dashboards/alertas do Grafana (detalhamento fino, via `backend-mentor` na Sprint 9) e o mapeamento de idempotência (`<ponto_critico id="idempotencia-revisao">`, Sprint 10).

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
- [x] 2.3 Registro de sessões de estudo (acertos/erros, timestamps) para alimentar estatísticas futuras — entidade `CardReview` (um evento por revisão, não uma "sessão" agregada — mesma granularidade do `revlog` do Anki; deliberadamente distinta de `GenerationSession`)
- [x] 2.4 Índices obrigatórios: deck, categoria, tag de relacionamento deck/card — `IndexDefinitions` em `schemas.py`, agora fonte única também para `MongoDBConnectionManager.create_indexes()`
- [x] 2.5 Serializers magros, herdáveis, sem boilerplate desnecessário — `serializers.Serializer` manuais (não `ModelSerializer`, que exige Model Django real)
- [x] 2.6 Django management command de seed: múltiplos usuários/tenants, decks/categorias variadas, cards com históricos de acerto/erro, datas passadas/recentes/futuras — protegido contra execução em produção, idempotente ou com `--reset` — `seed_decks` (validado rodando de verdade contra Mongo/Postgres reais)
- [x] 2.7 Testar comando de seed e a proteção contra produção explicitamente — `test_seed_command.py`; **28/28 testes passando** (Sprint 1 + 2)

**Nota de implementação**: isolamento multi-tenant em MongoDB precisou de mecanismo próprio (não o `TenantOwnedModel` da Sprint 1, que é ORM/Postgres-only) — `owner_id` obrigatório em toda assinatura de método de repositório. Um bug real de produção foi descoberto e corrigido durante a verificação end-to-end via HTTP: `AsyncIOMotorClient` ficava preso ao event loop em que era criado, e `async_to_sync` cria um loop novo a cada chamada — quebrava a partir da segunda/terceira chamada bridged do processo (ver Risks em `openspec/changes/sprint-2-decks-cards/design.md`).

*Critérios de aceite relevantes: 11.*

---

### Sprint 3 — Frontend Base & Home Dashboard

**Objetivo**: primeira superfície visual real do sistema, consumindo a API já funcional.

- [ ] 3.1 Scaffold da SPA React + pipeline de build
- [ ] 3.2 Consultar `design_system/design-system.html` e extrair os tokens antes de implementar qualquer tela
- [ ] 3.3 Home: último deck estudado, meta de estudo + % alcançado, gráfico de estatísticas (client-side, consumindo API do Django)
- [ ] 3.4 Exportação do gráfico da home para PDF
- [ ] 3.5 Menu lateral: decks, categorias, geração de relatórios, chat com agente de IA (placeholder até Sprint 5)
- [ ] 3.6 Auditoria de consistência visual contra o design system

*Critérios de aceite relevantes: 12.*

---

### Sprint 4 — Exportação Anki & Microsserviço de Documentos

**Objetivo**: fechar o ciclo do microsserviço de documentos já reclassificado na Sprint 0, ligando-o de ponta a ponta.

- [ ] 4.1 Endpoint Django que dispara (via Celery) a geração de `.apkg` no microsserviço de documentos
- [ ] 4.2 Circuit breaker + retry exponencial na chamada Django → microsserviço de documentos
- [ ] 4.3 Contrato de payload/resposta documentado entre Django e o microsserviço
- [ ] 4.4 Geração de PDF genérica no mesmo microsserviço (reaproveitada nas Sprints 3 e 7)
- [ ] 4.5 Validar `.apkg` gerado abrindo no Anki real

*Critérios de aceite relevantes: 2, 7, 9.*

---

### Sprint 5 — Agente de IA (LangChain/LangGraph)

**Objetivo**: a funcionalidade de maior risco/novidade técnica — só começa depois que decks/cards (Sprint 2) está sólido.

- [ ] 5.1 Microsserviço FastAPI do agente (LangChain/LangGraph), padrão MVC
- [ ] 5.2 Restrição de domínio fechado: só cards/decks/feedback de estudo — recusar qualquer pedido fora disso (ver `<escopo_agente_ia>`)
- [ ] 5.3 Limite rígido de 100 caracteres por card gerado, com descarte automático acima disso
- [ ] 5.4 Toda ação do agente passa pelas rotas de API existentes, com permissão especial dedicada — nunca acesso direto ao banco
- [ ] 5.5 `created_by`/`updated_by` = `"ai_agent_machine"` em todo recurso criado pelo agente
- [ ] 5.6 Defesas contra prompt injection (redefinição de papel, extração de dados de outros tenants)
- [ ] 5.7 Feedback diário na home + sugestão de novos cards/decks, sempre assíncrono via Celery
- [ ] 5.8 Testes cobrindo os exemplos adequado/inadequado/uso indevido já definidos em `<exemplos_de_uso>`

*Critérios de aceite relevantes: 2, 3, 4, 5.*

---

### Sprint 6 — Notificações WhatsApp (Evolution API)

**Objetivo**: último microsserviço da ordem definida — mais desacoplado do resto, entra por último de propósito.

- [ ] 6.1 Microsserviço FastAPI de integração com a Evolution API, padrão MVC
- [ ] 6.2 Envio de lembrete de estudo respeitando a meta de tempo definida pelo usuário
- [ ] 6.3 Disparo assíncrono via Celery (Celery Beat para agendamento periódico)
- [ ] 6.4 Circuit breaker + retry + DLQ na comunicação com a Evolution API

*Critérios de aceite relevantes: 2, 9.*

---

### Sprint 7 — Relatório Semanal por E-mail

**Objetivo**: fecha o loop de feedback do produto, reaproveitando o gerador de documentos (Sprint 4) e as estatísticas (Sprint 2).

- [ ] 7.1 Task Celery Beat semanal que coleta estatísticas de estudo do período
- [ ] 7.2 Geração do PDF do relatório via microsserviço de documentos
- [ ] 7.3 Resumo textual de evolução (pode reaproveitar o agente de IA da Sprint 5, dentro do escopo permitido)
- [ ] 7.4 Envio automático por e-mail, sem intervenção manual

*Critérios de aceite relevantes: 2, 6.*

---

### Sprint 8 — Deploy Real (VPS + S3 + Domínio)

**Objetivo**: tirar o sistema do "só roda local" e colocá-lo no ar de verdade.

- [ ] 8.1 `docker-compose.yml` de produção + processo de deploy (SSH + compose) na VPS Hostinger
- [ ] 8.2 Bucket S3 de hospedagem estática do frontend + pipeline de build/upload (GitHub Actions)
- [ ] 8.3 Compra do domínio via Cloudflare (sem pressa — só quando o usuário decidir) + configuração de DNS
- [ ] 8.4 Fluxo de deploy baseado em tags via GitHub Actions
- [ ] 8.5 Confirmar preço de renovação da Hostinger antes de qualquer contratação anual

*Critérios de aceite relevantes: 10.*

---

### Sprint 9 — Observabilidade

**Objetivo**: visibilidade operacional do sistema real em produção.

- [ ] 9.1 Logs estruturados JSON com `request_id` propagado, no Django e nos microsserviços
- [ ] 9.2 `django-prometheus` no Django + instrumentação equivalente em cada FastAPI
- [ ] 9.3 `node_exporter` na VPS
- [ ] 9.4 Exporter de RabbitMQ/Celery, com foco em profundidade de fila e de DLQ
- [ ] 9.5 **Mentoria via `backend-mentor`**: decidir quais dashboards Grafana montar primeiro e a política de alertas (decisão ainda pendente — `dashboards-alertas-grafana`)
- [ ] 9.6 Montar os dashboards e alertas decididos na 9.5

*Critérios de aceite relevantes: nenhum específico, mas suporta a operação de todos os demais.*

---

### Sprint 10 — Hardening & Revisão Final

**Objetivo**: fechar as pontas soltas que só fazem sentido revisar com o sistema inteiro construído.

- [ ] 10.1 Mapear quais operações precisam de garantia de idempotência (consumers de fila, tasks Celery, WhatsApp, geração de PDF) — resolve `<ponto_critico id="idempotencia-revisao">`
- [ ] 10.2 Implementar as proteções de idempotência mapeadas em 10.1
- [ ] 10.3 Auditoria final de isolamento multi-tenant em toda query/serializer/endpoint
- [ ] 10.4 Testar circuit breaker + retry exponencial simulando indisponibilidade de cada microsserviço
- [ ] 10.5 Checklist final contra os 12 itens de `<criterios_de_aceite>`
- [ ] 10.6 Revisão de segurança: permissões de arquivos/mídia, segredos fora do código-fonte

---

## 8. Trilhas de Aprendizado Paralelas (fora do roadmap principal)

Não bloqueiam nenhuma sprint acima — conduzidas via `backend-mentor` quando o usuário decidir retomar cada assunto:

- [ ] **Terraform + AWS**: projeto de estudo isolado, começando pelo state backend (S3 + DynamoDB) e um compute mínimo free-tier.
- [ ] **Kubernetes**: primeiro contato do usuário com a ferramenta — começar por `kind`/`minikube` local antes de qualquer cluster com IP público. (Ver memória: usuário pediu para retomar esse assunto mais tarde.)

---

## 9. Ordem de Execução

```
Sprint 0 (fundação) → Sprint 1 (auth/multi-tenant) → Sprint 2 (decks/cards)
   → Sprint 3 (frontend/home) → Sprint 4 (exportação Anki/documentos)
   → Sprint 5 (IA) → Sprint 6 (WhatsApp) → Sprint 7 (relatório semanal)
   → Sprint 8 (deploy real) → Sprint 9 (observabilidade) → Sprint 10 (hardening)
```

Esta ordem segue `<instrucoes_de_execucao>` item 3 de `PROMPT_REFINADO.md` e a ordem de microsserviços já decidida (`ordem-microservicos`). Cada sprint DEVE ser entregue e validada antes de avançar para a próxima — nunca pular etapas de segurança em nome de velocidade.
