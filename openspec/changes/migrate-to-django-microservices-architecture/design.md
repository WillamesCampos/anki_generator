## Context

O repositório contém hoje um monólito FastAPI incompleto, não a arquitetura descrita em `PROMPT_REFINADO.md`. Levantamento factual do estado atual:

- **Backend principal**: não existe Django em nenhum lugar do código (zero hits). O que existe é FastAPI (`main.py` → `presentation/api/main.py`), com um único endpoint real (`GET /health/`). CRUD de deck/card, autenticação, multi-tenant — tudo aspiracional, nada implementado.
- **Domínio**: existem DUAS estruturas de domínio concorrentes, ambas em `legacy/` (não acessíveis da raiz): (a) uma versão antiga/flat (`legacy/domain/models.py` + `legacy/services/anki_deck_generator/*`) e (b) uma versão mais madura em clean architecture (`legacy/domain/{entities,value_objects,repositories}` + `legacy/infrastructure/{database,repositories}`, com `CardRepository`/`DeckRepository`/`GenerationSessionRepository` via Motor). A raiz do projeto (`shared/`) só tem `settings.py` e `exceptions.py` — nenhuma entidade de domínio.
- **Persistência**: MongoDB é o padrão real (Motor/pymongo em `legacy/infrastructure`, `test_mongodb_integration.py`), mas o `Makefile` sobe um container **Postgres** (`ankigen_db`) que não é usado por nenhum código — inconsistência a resolver.
- **Geração de cards**: `generator_v2.py` é um script standalone funcional (genanki + gTTS) que não está integrado a nenhuma camada de domínio ou API — é a prova de conceito da funcionalidade de exportação Anki.
- **Infra**: não há Dockerfile/docker-compose na raiz (só em `legacy/`), não há Terraform em lugar nenhum, não há Celery/Redis/RabbitMQ/Kafka, não há Prometheus/Grafana, não há CI/CD.
- **Dependências**: `pyproject.toml` (Poetry) e `requirements.txt` (pip freeze antigo) estão dessincronizados — libs diferentes em cada um.

O usuário decidiu que a arquitetura vai mudar drasticamente (Django como backend principal, conforme `PROMPT_REFINADO.md`), mas quer reaproveitar o que já foi validado: o domínio em clean architecture de `legacy/`, os repositórios Mongo, e a lógica de geração de card/áudio/exportação `.apkg`.

## Goals / Non-Goals

**Goals:**
- Estabelecer a fundação de arquitetura (Django `core` + `apps/`, microsserviços FastAPI satélites) exigida por `PROMPT_REFINADO.md`.
- Migrar e consolidar em um único lugar o domínio reaproveitável hoje órfão em `legacy/`, eliminando a duplicidade de estruturas.
- Corrigir inconsistências existentes no repo (Postgres órfão no Makefile, deps dessincronizadas) antes de construir por cima delas.
- Trazer Docker/docker-compose para a raiz, non-root, com entrypoint.
- Estabelecer a fundação de deploy real do sistema (VPS + Docker Compose) e de hospedagem do frontend (AWS S3 + React), além de observabilidade (Prometheus + Grafana), com o system design conduzido de forma didática via skill `backend-mentor`, pois o usuário não tem domínio prévio nele.
- Produzir um documento de system design (componentes, limites de serviço, fluxo de dados) da arquitetura-alvo antes de qualquer código de feature ser escrito.

**Non-Goals (ficam para changes futuros, na ordem definida em `<instrucoes_de_execucao>` de `PROMPT_REFINADO.md`):**
- CRUD de decks/cards, autenticação/multi-tenant end-to-end, agente de IA (LangChain/LangGraph), notificação WhatsApp (Evolution API), relatório semanal em PDF, exportação `.apkg` via API.
- Deploy do backend na AWS via Terraform — decidido explicitamente como **fora de escopo** deste sistema; Terraform+AWS viram um projeto de estudo separado, menor e mais simples, feito quando o usuário estiver focado nesse aprendizado. O deploy real deste sistema é em VPS.
- Implementação final/detalhada de dashboards Grafana (esta change entrega a *fundação* — decisão de stack, esqueleto de configuração, primeira métrica de exemplo — não o deploy completo em produção).
- Microsserviço de gráficos/estatísticas — decidido que **não existe**; gráficos são renderizados client-side no React, consumindo a API do Django.
- Migração de dados reais (não há dados de produção hoje).

## Decisions

### D1 — Django como backend principal; FastAPI atual torna-se microsserviço satélite
`PROMPT_REFINADO.md` já mandata Django+DRF como backend principal. O FastAPI existente (`presentation/api/`) não é descartado — é realocado como o microsserviço de **geração de documentos / exportação Anki**, já que `generator_v2.py` prova que essa lógica (genanki + gTTS) funciona e é isolada por natureza (não precisa de acesso direto ao domínio multi-tenant, só recebe um payload e devolve um arquivo).
- **Alternativa considerada**: manter FastAPI como principal e adicionar Django só para admin. Rejeitada — contradiz `PROMPT_REFINADO.md` (`<backend_principal>`), que é a fonte de verdade acordada com o usuário.

### D2 — Domínio consolidado a partir da versão clean-architecture de `legacy/`
A versão mais madura (`legacy/domain/entities` + `legacy/infrastructure/repositories`, com Motor) é promovida para dentro de `apps/` (ex.: `apps/decks/domain/`, `apps/decks/infrastructure/`), adaptando os repositórios para o padrão de app Django. A versão flat antiga (`legacy/domain/models.py`, `legacy/services/anki_deck_generator/`) e o `legacy/main.py` quebrado são descartados.
- **Alternativa considerada**: reescrever o domínio do zero dentro de `apps/`. Rejeitada — o domínio em `legacy/` já foi modelado com cuidado (value objects, serviços de qualidade/duplicidade de card) e reescrever destruiria trabalho validado sem ganho.

### D3 — Persistência poliglota: MongoDB para deck/card/estatísticas, PostgreSQL para o subsistema interno do Django
Confirma o que já está em `PROMPT_REFINADO.md` (`<persistencia>`). MongoDB via Motor permanece a persistência de deck/card/estatísticas. O Django usa **PostgreSQL** dedicado para `auth`/`Permission`/`Group`/sessões/admin/migrations — o framework assume um backend relacional para esse subsistema, e SQLite fica descartado mesmo em dev (roda em container Docker também localmente, por paridade dev/prod). O alvo `db` do `Makefile`, que hoje sobe um Postgres órfão não referenciado por código nenhum, é mantido mas reapontado para essa finalidade real (auth do Django), em vez de removido.
- **Alternativa considerada**: usar SQLite em desenvolvimento local e só introduzir Postgres em produção. Rejeitada — diferença de comportamento entre motores (locking, tipos, concorrência) é uma fonte clássica de bug que só aparece em produção; o custo de rodar Postgres local via Docker é baixo.
- **Alternativa considerada**: forçar Mongo a cobrir também `auth`/`Permission`/`Group` via adapter (ex.: Djongo). Rejeitada — pouco mantido, briga desnecessária com o ORM do Django por um ganho que não existe (não há motivo técnico para não ter dois bancos).

### D4 — Deploy real em VPS; Terraform+AWS desacoplado como projeto de estudo separado; AWS permanece só para S3
Sessão de mentoria (`backend-mentor`) concluiu que AWS via Terraform não é justificado tecnicamente para este sistema — é uma escolha de aprendizado, não uma necessidade do projeto. O usuário confirmou: o deploy real do backend (Django + microsserviços + Mongo + Redis) vai para uma **VPS** via Docker Compose; Terraform+AWS viram um projeto de estudo dedicado, menor e mais simples, feito à parte, sem bloquear o deploy real nem esta change. A AWS continua sendo usada, mas só para **S3** (hospedagem estática do frontend React) — que é uma decisão definitiva, não uma escolha de aprendizado.
- **Alternativa considerada**: provisionar a infraestrutura de produção inteira via Terraform na AWS desde já. Rejeitada pelo usuário — custo operacional (NAT Gateway, RDS, etc.) e complexidade não justificados para aprender Terraform; misturar "aprender a ferramenta" com "manter produção" é mais arriscado que separar os dois.
- **Alternativa considerada**: usar Route53 para o domínio, já que uma parte da AWS (S3) já está em uso. Descartada pelo usuário em favor de Cloudflare (registrador mais barato, sem markup, DNS gratuito, desacoplado do provedor de deploy).

### D5 — Gráficos/estatísticas: client-side no React, sem microsserviço dedicado
Resolve o item `stack-graficos` de `<decisoes_pendentes>` em `PROMPT_REFINADO.md`. Em vez de um microsserviço FastAPI dedicado (Plotly ou similar), os gráficos são renderizados no frontend React a partir dos dados já expostos pelas APIs do Django (`/api/v1/...`) — sem componente de servidor adicional para isso.
- **Alternativa considerada**: microsserviço FastAPI de gráficos com Plotly/servidor. Rejeitada — não há motivo técnico real (a régua "é uma fronteira de negócio ou só conveniência técnica?" não passa); teria sido complexidade adicional sem ganho, já que o React já vai consumir a API do Django para tudo mais.

### D6 — Hospedagem do frontend: AWS S3 (estático) + React
Resolve o item `hospedagem-frontend` de `<decisoes_pendentes>` em `PROMPT_REFINADO.md`. O frontend é uma SPA React, buildada estaticamente e hospedada em um bucket S3 (não Django Templates server-side).
- **Alternativa considerada**: servir o frontend via Django Templates. Rejeitada — o usuário já decidiu por uma SPA React desacoplada, consumindo a API do Django via REST.

### D7 — Mensageria: RabbitMQ, não Kafka
Resolve `tecnologia-fila`. O padrão de uso do projeto é fila de tarefas (Celery dispara doc-generation/IA/WhatsApp e espera confirmação de processamento) — não log de eventos replayable em alto volume. RabbitMQ é o parceiro natural do Celery para esse padrão.
- **Alternativa considerada**: Kafka. Rejeitada — throughput massivo via partições, replay de eventos e múltiplos consumer groups independentes são recursos que este projeto não usa; adicionar Kafka seria complexidade operacional sem retorno.

### D8 — Provedor de VPS: Hostinger
Resolve parte de `provedor-vps` (a escolha de provedor; a forma de orquestração dos containers continua em aberto — ver Open Questions). Comparando planos de ~4GB RAM: DigitalOcean cobra ~$24/mês (2 vCPU/4GB); Hostinger oferece ~$5-7/mês para capacidade equivalente ou maior. Diferença grande o suficiente para pesar num projeto pessoal.
- **Alternativa considerada**: DigitalOcean, pela vantagem de documentação/ecossistema mais maduro para quem está aprendendo self-hosting. Rejeitada pelo usuário — a diferença de custo foi o critério decisivo.
- **Ressalva registrada**: o preço de entrada da Hostinger costuma ser promocional do primeiro ciclo; o preço de renovação DEVE ser confirmado antes da contratação efetiva, para não ancorar a decisão num valor que não se repete.

### D9 — Meta de escala: 10.000 usuários ativos (requests esporádicos), não conexões persistentes simultâneas
Decisão de **desenho**, não de infraestrutura provisionada agora. "10k usuários simultâneos" foi esclarecido na sessão de mentoria como usuários ativos gerando requests ao longo do tempo (throughput moderado), não 10k conexões persistentes abertas (ex.: WebSocket) — essa segunda leitura exigiria uma camada de conexão persistente (Django Channels + Redis pub/sub) que o projeto não precisa hoje.
- **Implicação de design**: Django deve permanecer stateless (sem estado de sessão/negócio preso à memória de um processo), para permitir escalar horizontalmente depois sem reescrita.
- **Implicação de infraestrutura**: nenhuma — a VPS Hostinger contratada NÃO precisa refletir essa meta agora; provisionar para 10k hoje seria desperdício de orçamento.

### D10 — Observabilidade: ordem de instrumentação definida
Resolve o detalhamento antes coberto por `stack-observabilidade-detalhamento`. Ordem: (1) logs estruturados JSON com `request_id` propagado — pilar mais barato, maior retorno imediato de debugging; (2) métricas via `django-prometheus` (Django) e equivalente em cada FastAPI (taxa de erro, latência p50/p95/p99, throughput); (3) `node_exporter` para métricas de host da VPS; (4) exporter de RabbitMQ/Celery expondo profundidade de fila e, especificamente, profundidade de **DLQ** — dado o requisito obrigatório de retry/DLQ já existente em `PROMPT_REFINADO.md`. Dashboards Grafana específicos e política de alertas ficam para detalhamento posterior via `backend-mentor` (ver Open Questions).
- **Alternativa considerada**: começar direto por Prometheus/Grafana, pulando logs estruturados. Rejeitada — logs JSON com `request_id` são o pilar de menor custo/maior retorno para debugging do dia a dia; métricas respondem "está lento/com erro?", não "por quê".

### D11 — Orquestração na VPS: Docker Compose direto; Kubernetes desacoplado como projeto de estudo separado
Resolve `orquestracao-vps`. O usuário considerou Kubernetes para a VPS Hostinger, explicitamente por objetivo de aprendizado (primeiro contato dele com a ferramenta — nunca rodou nem `minikube`). Sessão de mentoria aplicou o mesmo princípio já usado para Terraform/AWS: **não aprender uma ferramenta de infraestrutura nova em cima do sistema que precisa continuar no ar**. O control plane do Kubernetes (mesmo k3s) consome CPU/RAM que competem com os serviços reais numa VPS pequena, e um erro de aprendizado ali é uma categoria de risco diferente de um erro de Terraform (Terraform erra e o sistema já rodando continua rodando; Kubernetes erra e o sistema pode cair junto). O deploy real usa `docker compose` direto. O aprendizado de Kubernetes fica para depois, começando por `kind`/`minikube` local (sem custo, sem risco ao sistema real) — usuário pediu explicitamente para retomar esse assunto em conversa futura.
- **Alternativa considerada**: k3s na própria VPS Hostinger de produção. Rejeitada — mistura as duas metas (aprender a ferramenta + manter produção estável), mesmo racional do Terraform.
- **Alternativa considerada**: Coolify/Dokploy como camada leve sobre Docker Compose. Não escolhida nem descartada — o usuário foi direto para a pergunta de Kubernetes; Coolify/Dokploy podem voltar à mesa se o `docker compose` puro se mostrar insuficiente para o fluxo de deploy.

### D12 — Rate limiting: 3 req/s; idempotência marcada para revisão futura
Resolve `taxa-rate-limiting`: 3 requests/segundo por usuário/cliente no Django. Na mesma resposta, o usuário levantou que idempotência precisa ser revisitada dado que agora há retry exponencial, DLQ e rate limiting todos definidos — registrado como `<ponto_critico id="idempotencia-revisao">` em `PROMPT_REFINADO.md`, não como decisão fechada: ainda falta mapear quais operações (consumo de fila, tasks Celery, envio de WhatsApp, geração de PDF) precisam de proteção contra efeito duplicado em reprocessamento. Fica para uma change futura dedicada, não para esta fundação.

## Risks / Trade-offs

- **[Risco]** Migrar o domínio de `legacy/` pode trazer acoplamentos implícitos (ex.: repositórios assumindo um `mongodb_connection` global) que não se encaixam limpamente no padrão de apps Django. → **Mitigação**: migrar um agregado por vez (ex.: `Deck` primeiro), validando com teste de integração equivalente ao `test_mongodb_integration.py` antes de migrar o próximo.
- **[Risco]** Reclassificar o FastAPI de "principal" para "microsserviço satélite" pode gerar confusão sobre contratos de API (quem chama quem). → **Mitigação**: o documento de system design (task desta change) define explicitamente as fronteiras e contratos antes de qualquer código novo.
- **[Risco]** Usuário está aprendendo Terraform/AWS/domínio pela primeira vez — risco de gastar dinheiro real (compra de domínio, recursos AWS) por decisão apressada. → **Mitigação**: mentoria via `backend-mentor` acontece ANTES de qualquer ação que envolva custo real, e cada decisão de custo é confirmada explicitamente. Domínio já tem registrador decidido (Cloudflare) mas sem pressa de compra; Terraform/AWS ficam isolados como projeto de estudo, então erros de custo nesse aprendizado não afetam o sistema em produção (que está na VPS).
- **[Risco]** Rodar em VPS via Docker Compose puro tem menos garantias operacionais que uma cloud gerenciada (sem auto-healing, backup automático, etc., a menos que configurado manualmente). → **Mitigação**: aceitável para o estágio atual do projeto (pessoal/portfólio); backups e resiliência entram como tarefa explícita quando o sistema tiver dados reais em produção, não nesta fundação.
- **[Trade-off]** Esta change entrega apenas a fundação (esqueleto), não o sistema funcional — significa que, por um tempo, nenhuma feature de produto avança. Aceito conscientemente porque construir features sobre uma base inconsistente (dois domínios concorrentes, DB errado no Makefile) geraria retrabalho maior depois.

## Migration Plan

1. Congelar `legacy/` como referência somente-leitura (não editar in-place; copiar o que for reaproveitado).
2. Criar o projeto Django (`core/`) e a pasta `apps/`, com o primeiro app (`apps/decks/`) recebendo o domínio consolidado (D2), usando PostgreSQL (D3) como banco de `auth`/`Permission`/`Group`.
3. Ajustar `Makefile`, `docker-compose.yml` (novo, na raiz, com Postgres + Mongo + Redis + RabbitMQ) e unificar `pyproject.toml`/`requirements.txt`.
4. Realocar o FastAPI atual para `microservices/document-generator/` (ou nome equivalente definido no system design), mantendo `generator_v2.py` como base da lógica de exportação.
5. Adicionar Celery + RabbitMQ (D7) + Redis ao `docker-compose.yml` (sem tasks reais ainda — só a fundação de infraestrutura).
6. Sessão de mentoria (`backend-mentor`) para desenhar o system design da arquitetura-alvo — **concluída**, ver decisões D4–D12 acima.
7. Configurar deploy do backend na VPS Hostinger (D8, Docker Compose) e o pipeline de build/upload do frontend React para o bucket S3.
8. Instrumentar logs estruturados + métricas na ordem definida em D10.
9. Remover `legacy/` do repositório após confirmação de que nada relevante ficou para trás.
- **Rollback**: como não há ambiente de produção nem dados reais em jogo, o rollback é `git revert` da branch da change — sem risco de perda de dados.

## Open Questions

- Quais dashboards Grafana montar primeiro e qual política de alertas adotar (o que exige ação humana imediata vs. o que é só painel)? — detalhamento fino a conduzir via `backend-mentor` quando essa etapa do `tasks.md` começar.
- Quais operações exigem garantia de idempotência (consumers de fila, tasks Celery, envio de WhatsApp, geração de PDF)? — levantado pelo usuário junto com a decisão de rate limiting (D12), ainda não mapeado; fica para change futura dedicada.
