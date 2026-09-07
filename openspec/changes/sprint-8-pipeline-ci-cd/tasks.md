## 1. Backend — lint tooling

- [x] 1.1 `poetry add --group dev black` em `django/`
- [x] 1.2 `[tool.black]` em `django/pyproject.toml` (ver D2 em design.md)
- [x] 1.3 Rodar `black .` (sem `--check`) uma vez sobre o código existente e commitar a reformatação, antes de ativar o gate (ver Risco em design.md)
- [x] 1.4 `.pre-commit-config.yaml` na raiz do repo, com o hook oficial do `black`

## 2. GitHub Actions — workflow

- [x] 2.1 `.github/workflows/ci.yml` — gatilhos `pull_request` (visando `main`) e `push` (`branches: [main]`)
- [x] 2.2 Job `lint`: `black --check .` no backend + `npm run lint` no frontend
- [x] 2.3 Job `backend-test`: `pytest apps/`, com Postgres/MongoDB/Redis como service containers (ver D3 em design.md)
- [x] 2.4 Job `frontend-test`: `npm test` (Vitest)
- [x] 2.5 Os 3 jobs rodam em paralelo, cada um como status check independente no PR

## 3. Documentação

- [x] 3.1 Badge de status do CI no `README.md`
- [x] 3.2 Atualizar `PRD.md` (Sprint 8) marcando as tarefas concluídas
- [x] 3.3 Atualizar `CHANGELOG.md` com a entrada `[Sprint 8]`
