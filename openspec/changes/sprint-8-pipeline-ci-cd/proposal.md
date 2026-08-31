## Why

Todas as sprints até aqui (0-7) foram mescladas na `main` sem nenhum gate automatizado — os testes existentes (`pytest` desde a Sprint 1, Vitest desde a Sprint 4) só rodam se alguém lembrar de rodar `make test`/`make frontend-test` localmente antes do merge. Inserida aqui de propósito, antes da Sprint 9 (tela de estudo) e da Sprint 10 (estatísticas), pra que toda sprint daqui pra frente já nasça protegida por CI. Aproveitando o escopo, fecha também uma regra mandatória (`<regra_obrigatoria id="ferramentas-lint">` em `PROMPT_REFINADO.md`) declarada desde o início do projeto mas nunca implementada: o backend não tem `black` nem `pre-commit` configurados — não existe hoje nenhuma etapa de lint possível pro Django, só pro frontend (`eslint`, via `npm run lint`).

## What Changes

- Adiciona `black` como dependência de desenvolvimento do Django (`django/pyproject.toml`) e `.pre-commit-config.yaml` na raiz do projeto, cobrindo a regra mandatória de lint que faltava.
- Cria o workflow do GitHub Actions (`.github/workflows/ci.yml`) com 3 jobs independentes — `lint` (black --check no backend + eslint no frontend), `backend-test` (`pytest`, com Postgres/MongoDB/Redis como service containers) e `frontend-test` (Vitest) — todos rodando a mesma suíte em 2 gatilhos distintos: `pull_request` (visando `main`) e `push` (em `main`, pós-merge).
- Badge de status do CI no `README.md`.

## Capabilities

### New Capabilities
- `backend-lint-tooling`: `black` + `.pre-commit-config.yaml` configurados no projeto Django, fechando a regra mandatória de lint/PEP-8 que estava pendente desde `PROMPT_REFINADO.md`.
- `ci-test-pipeline`: workflow do GitHub Actions com 3 jobs (lint, backend-test, frontend-test), disparado tanto em PRs quanto em merges na `main`, usando a mesma suíte de testes nos dois gatilhos.

### Modified Capabilities
(nenhuma — não há capability canônica de CI/testes arquivada em `openspec/specs/`)

## Impact

- Backend: `django/pyproject.toml` (nova dependência de dev `black`), `django/pyproject.toml` ou `.black.toml`/`pyproject.toml` raiz (config do `black`).
- Raiz do repo: `.pre-commit-config.yaml` (novo), `.github/workflows/ci.yml` (novo), `README.md` (badge).
- Nenhuma mudança de contrato de API, schema de banco ou comportamento de produto — sprint inteiramente de tooling/infraestrutura de desenvolvimento.
- Fora de escopo, por decisão explícita: ampliar a cobertura de testes existente (novos testes pra API client, hooks, telas específicas) — ver `design.md`. Essa sprint garante que os testes *que já existem* rodem automaticamente; escrever mais testes continua acontecendo ao fim de cada sprint futura, como já é o processo hoje.
