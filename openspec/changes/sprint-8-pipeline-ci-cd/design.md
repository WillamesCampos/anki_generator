## Context

Esta sprint ocupa o lugar que originalmente era da Sprint 10 ("Testes & CI/CD") no roadmap — trazida pra Sprint 8 por decisão explícita do usuário, empurrando a antiga Sprint 8 (Tela de Estudo) pra Sprint 9 e a antiga Sprint 9 (Estatísticas por Deck) pra Sprint 10. Motivo: nenhuma sprint daqui em diante deve ser mesclada na `main` sem gate automatizado, e quanto antes o pipeline existir, menos sprints ficam sem essa proteção.

Estado atual, confirmado por leitura direta do repo:
- Backend: `pytest` configurado desde a Sprint 1 (`django/pyproject.toml`, `make test`), sem nenhum lint configurado (`grep` por `black`/`flake8`/`ruff` no `pyproject.toml` não retorna nada, não existe `.pre-commit-config.yaml`).
- Frontend: Vitest + React Testing Library desde a Sprint 4 (`make frontend-test`), ESLint já configurado (`make frontend-lint`).
- Não existe `.github/` no repo — nenhum workflow de CI hoje.

## Goals / Non-Goals

**Goals:**
- Toda PR contra `main` roda lint + testes de backend + testes de frontend automaticamente, como check obrigatório.
- Todo merge em `main` roda a mesma suíte de novo, como segunda checagem pós-merge (gatilho `push` em `main`).
- Fechar a lacuna de lint do backend (`black` + `pre-commit`), mandatória desde `PROMPT_REFINADO.md` mas nunca implementada.

**Non-Goals:**
- Ampliar a cobertura de testes existente (testes novos pra API client, hooks, telas específicas) — decisão explícita do usuário: esta sprint é sobre a *pipeline* rodar o que já existe, não sobre escrever mais testes. Cobertura cresce organicamente a cada sprint futura, como já é o processo (`[[feedback_testing_workflow]]`).
- Deploy automatizado (CD de verdade) a partir do merge em `main` — fora de escopo; a Sprint 15 (Deploy Real) é quem decide como o deploy pra VPS acontece. O gatilho `push`/`main` desta sprint só roda testes, não publica nada.
- Relatório de cobertura de testes com limites mínimos (thresholds) — não pedido pelo usuário nesta rodada; pode entrar numa sprint futura se virar necessidade real.
- Ruff/flake8 além do `black` — a regra mandatória em `PROMPT_REFINADO.md` cita explicitamente só `black` + `pre-commit`; não adicionar ferramenta não pedida.

## Decisions

### D1 — Um workflow, 3 jobs independentes (lint / backend-test / frontend-test), 2 gatilhos
Único arquivo `.github/workflows/ci.yml`, com `on: [pull_request, push]` (`push` restrito a `branches: [main]`) e 3 jobs paralelos, cada um rodando em ambos os gatilhos:
- `lint`: `black --check .` no backend (`django/`) + `npm run lint` no frontend.
- `backend-test`: `pytest apps/`, com Postgres, MongoDB e Redis como service containers do job (mesmas versões do `docker-compose.yml`).
- `frontend-test`: `npm test` (Vitest).

**Alternativa descartada**: um job único rodando tudo em sequência. Rejeitada — jobs paralelos dão feedback mais rápido (falha de lint não espera o backend terminar) e status checks separados no PR deixam claro qual etapa quebrou.

**Alternativa descartada**: dois workflows separados (um pra PR, outro pra push em `main`). Rejeitada — duplicaria a definição dos 3 jobs; um workflow só com dois gatilhos no `on:` já cobre o pedido do usuário ("mesma suíte rodando nas duas etapas") sem duplicação.

### D2 — `black` sem `ruff`/`flake8`, config mínima
Adiciona `black` como dependência de dev (`poetry add --group dev black` em `django/`), com `[tool.black]` no `pyproject.toml` existente (sem opções customizadas além de `line-length` se necessário pra bater com o código já escrito). `.pre-commit-config.yaml` na raiz roda o hook oficial do `black`. O job `lint` do CI roda `black --check .` diretamente (não via `pre-commit run`), pra não depender de instalar o `pre-commit` no runner por uma checagem só — mais simples e mais rápido.

**Alternativa descartada**: `pre-commit run --all-files` no CI. Rejeitada por ora — adiciona uma dependência (`pre-commit` no runner) sem ganho sobre chamar `black --check` direto, já que hoje só há um hook configurado.

### D3 — Service containers no job de backend, não Docker Compose
O job `backend-test` usa a sintaxe nativa de `services:` do GitHub Actions (Postgres/MongoDB/Redis como containers do job), não `docker compose up`. Mais rápido (paralelo ao checkout, sem overhead do compose) e é o padrão recomendado do GitHub Actions pra dependências de teste.

## Risks / Trade-offs

- **[Risco]** `black --check` pode falhar em massa na primeira execução se o código atual (Sprints 0-7) não estiver formatado de acordo. → **Mitigação**: rodar `black .` (sem `--check`) uma vez, localmente, como parte da task de setup desta sprint, commitando a reformatação antes de ativar o gate no CI.
- **[Risco]** Rodar a suíte completa de novo no `push` em `main` (além do `pull_request`) é redundante quando o PR já passou nos mesmos testes antes do merge (commit idêntico). → **Aceito conscientemente**: decisão explícita do usuário ter as 2 etapas; serve como rede de segurança contra merges feitos fora do fluxo normal de PR (push direto, merge de branch desatualizada) e é barato (poucos minutos de CI).

## Migration Plan

Sem migração de dados. Setup de tooling (`black`, `pre-commit`, workflow do GitHub Actions) — não afeta código de produção nem schema. Uma reformatação única do código existente via `black .` é esperada como parte da implementação (ver Risco acima).
