## Why

O código atual é um monólito FastAPI incompleto (domínio parcial em `legacy/`, apenas um endpoint `/health/` funcional) que não reflete a arquitetura-alvo definida em `PROMPT_REFINADO.md`: Django/DRF como backend principal, microsserviços FastAPI satélites, MongoDB, Celery+Redis, mensageria com DLQ, observabilidade (Prometheus+Grafana) e deploy do sistema real em VPS, com frontend React estático hospedado em AWS S3. Antes de implementar qualquer funcionalidade nova (decks, IA, WhatsApp, relatórios), é preciso levantar os gaps entre o estado atual e o estado-alvo, decidir o que do código existente é reaproveitável, e resolver inconsistências já presentes no repo (ex.: `Makefile` aponta para Postgres enquanto todo o resto do projeto usa MongoDB).

## What Changes

- Formalizar Django como backend principal (`core` app + pasta `apps/`) — hoje inexistente no repositório (zero Django em todo o código).
- **BREAKING**: reclassificar o FastAPI atual (`main.py`, `presentation/api/`) de "aplicação principal" para um dos microsserviços satélites (ex.: geração de documentos/exportação Anki); ele deixa de ser o entrypoint do sistema.
- Consolidar em um único local canônico o domínio hoje duplicado/órfão em `legacy/domain/` e `legacy/infrastructure/` (entities `Card`/`Deck`/`GenerationSession`, value objects, repositórios Mongo via Motor, serviços de qualidade/duplicidade de cards) — nada disso está hoje acessível a partir da raiz do projeto.
- Resolver a inconsistência de banco de dados entre o `Makefile` (sobe container Postgres) e o restante do projeto (MongoDB via Motor/pymongo) — remover o alvo Postgres não utilizado.
- Trazer Docker/docker-compose para a raiz do projeto (hoje só existe em `legacy/docker-compose.yml`), com usuário non-root e script `entrypoint`, conforme já exigido em `PROMPT_REFINADO.md`.
- Introduzir Celery + Redis, mensageria (RabbitMQ ou Kafka — decisão pendente) com retry/DLQ, e circuit breaker com retry exponencial nas chamadas Django → microsserviço — nenhum destes existe hoje no código.
- Unificar a gestão de dependências (hoje `pyproject.toml` e `requirements.txt` estão dessincronizados, com libs diferentes em cada um).
- Adicionar fundação de observabilidade com Prometheus + Grafana (aprendizado guiado — ver `<observabilidade>` em `PROMPT_REFINADO.md`).
- **Decidido**: gráficos/estatísticas NÃO serão um microsserviço — renderização client-side no React, consumindo dados já expostos pela API do Django. Remove o item `stack-graficos` de `<decisoes_pendentes>`.
- **Decidido**: hospedagem do frontend confirmada como AWS S3 (SPA estática) + React. Remove o item `hospedagem-frontend` de `<decisoes_pendentes>`.
- **Decidido**: o deploy real do sistema (Django + microsserviços + Mongo + Redis) será em uma VPS via Docker Compose — não em AWS. Terraform + AWS deixam de ser o caminho de deploy deste sistema e passam a ser um projeto de estudo dedicado, separado e mais simples, feito quando o usuário estiver focado em aprender Terraform — não bloqueia esta change nem o deploy real.
- **Decidido**: domínio será comprado via Cloudflare (registrador), sem pressa de compra imediata.
- Adicionar fundação de deploy do sistema real: VPS + Docker Compose para o backend, AWS S3 para o build estático do frontend React.
- Produzir um documento de system design (diagrama de componentes, limites de serviço, fluxo de dados) para validar a nova arquitetura antes de codificar, conduzido de forma didática.
- Atualizar `PROMPT_REFINADO.md` com os gaps identificados e as decisões resultantes deste levantamento (nova seção de gaps de arquitetura).

## Capabilities

### New Capabilities

- `service-architecture-foundation`: estrutura Django (`core` + `apps/`) como backend principal, com os serviços FastAPI existentes/futuros reclassificados como microsserviços satélites e convenções de comunicação entre eles (contratos de API, autenticação de serviço-a-serviço). Gráficos/estatísticas explicitamente NÃO entram nessa lista de microsserviços — são client-side no React.
- `local-dev-environment`: ambiente de desenvolvimento local reprodutível — Docker/docker-compose (containers non-root, entrypoint), Makefile corrigido (sem Postgres órfão), Poetry (Django) + venv (microsserviços), carregamento de `.env` via `python-dotenv`.
- `domain-model-consolidation`: domínio único (entities, value objects, repositórios, serviços) migrado de `legacy/` para dentro da nova estrutura `apps/`, integrado ao MongoDB via Motor, eliminando as duas estruturas de domínio concorrentes hoje existentes.
- `deploy-observability-foundation`: fundação de deploy do sistema real em VPS (Docker Compose) + hospedagem estática do frontend React via AWS S3 + observabilidade (Prometheus + Grafana), entregue de forma mentorada/guiada via skill `backend-mentor`. Terraform + deploy completo na AWS ficam explicitamente fora desta fundação — tratados como projeto de estudo dedicado, separado e futuro.

### Modified Capabilities

_(nenhuma — não há specs existentes em `openspec/specs/`; este é o primeiro change do projeto)_

## Impact

- **Código afetado**: `main.py`, `presentation/`, `shared/` (migram para dentro de `core`/`apps/` ou são descontinuados), `legacy/*` (conteúdo reaproveitável é migrado, o restante é removido), `Makefile`, `pyproject.toml`/`requirements.txt` (unificados), `test_mongodb_integration.py` (caminhos de import corrigidos).
- **Código novo**: `core/` (projeto Django), `apps/` (apps Django), `Dockerfile`/`docker-compose.yml` na raiz (deploy em VPS), configuração de build/deploy do frontend React para AWS S3, configuração Prometheus + dashboards Grafana.
- **Dependências novas**: Django, Django REST Framework, Celery, Redis, cliente RabbitMQ/Kafka (a decidir).
- **Documentação**: `PROMPT_REFINADO.md` recebe os gaps/decisões deste levantamento; `README.md` e `ETAPAS_PROJETO.md` ficam desatualizados frente à nova arquitetura e precisarão de revisão em change futuro.
- **Aprendizado guiado**: system design desta arquitetura é tratado com explicações didáticas via skill `backend-mentor`, por ser área em que o usuário ainda não tem domínio. Terraform/AWS e compra de domínio (Cloudflare, sem pressa) também são mentorados, mas como projeto de estudo separado do deploy real deste sistema (que vai para VPS).
- **Fora de escopo deste change**: implementação de funcionalidades de produto (CRUD de decks/cards, agente de IA, WhatsApp, relatórios PDF, exportação Anki) — ficam para changes incrementais subsequentes, seguindo a ordem definida em `<instrucoes_de_execucao>` de `PROMPT_REFINADO.md`.
