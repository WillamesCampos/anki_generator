## 1. Backend — lint tooling

- [ ] 1.1 `poetry add --group dev black` em `django/`
- [ ] 1.2 `[tool.black]` em `django/pyproject.toml` (ver D2 em design.md)
- [ ] 1.3 Rodar `black .` (sem `--check`) uma vez sobre o código existente e commitar a reformatação, antes de ativar o gate (ver Risco em design.md)
- [ ] 1.4 `.pre-commit-config.yaml` na raiz do repo, com o hook oficial do `black`

## 2. GitHub Actions — workflow

- [ ] 2.1 `.github/workflows/ci.yml` — gatilhos `pull_request` (visando `main`) e `push` (`branches: [main]`)
- [ ] 2.2 Job `lint`: `black --check .` no backend + `npm run lint` no frontend
- [ ] 2.3 Job `backend-test`: `pytest apps/`, com Postgres/MongoDB/Redis como service containers (ver D3 em design.md)
- [ ] 2.4 Job `frontend-test`: `npm test` (Vitest)
- [ ] 2.5 Os 3 jobs rodam em paralelo, cada um como status check independente no PR

## 3. Documentação

- [ ] 3.1 Badge de status do CI no `README.md`
- [ ] 3.2 Atualizar `PRD.md` (Sprint 8) marcando as tarefas concluídas
- [ ] 3.3 Atualizar `CHANGELOG.md` com a entrada `[Sprint 8]`
