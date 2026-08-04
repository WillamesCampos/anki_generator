<div align="center">
    <img width="680" height="350" alt="Anki Generator Logo" src="https://github.com/user-attachments/assets/560c81d7-849d-41b8-a348-4dc08706628e" />
</div>

# 🎴 Anki Generator

Plataforma de flashcards inspirada no Anki, com um agente de IA que dá feedback de estudo, sugere novos cards/decks, envia lembretes via WhatsApp e gera relatórios periódicos de desempenho em PDF.

> A partir da **Sprint 0**, a arquitetura mudou drasticamente em relação às versões anteriores deste README: o projeto passou de um monólito FastAPI/Flask incompleto para Django como backend principal + microsserviços FastAPI satélites. Veja o porquê e o histórico completo das decisões em [PROMPT_REFINADO.md](./PROMPT_REFINADO.md).

## 📖 Documentação de referência

Este README é só uma porta de entrada. As fontes de verdade do projeto são:

- **[PROMPT_REFINADO.md](./PROMPT_REFINADO.md)** — especificação técnica mandatória: regras de arquitetura, decisões já tomadas (`<decisoes_resolvidas>`) e ainda pendentes (`<decisoes_pendentes>`). Qualquer dúvida de "como isso deve ser implementado" começa aqui.
- **[PRD.md](./PRD.md)** — roadmap do produto em sprints (checklist), da fundação até a última feature.
- **[design_system/design-system.html](./design_system/design-system.html)** — fonte única de verdade visual (cores, tipografia, componentes) para todo o frontend.
- **`openspec/changes/`** — propostas de arquitetura em formato spec-driven (proposal/design/specs/tasks), usadas para planejar e executar mudanças estruturais como a da Sprint 0.

## 🏗️ Arquitetura

```
Cliente (SPA React, hospedada em S3)
        │  REST /api/v1/...
        ▼
Django + DRF (django/core/ + django/apps/)  ──▶  PostgreSQL (auth/Permission/Group)
        │                                   ──▶  MongoDB (decks/cards/estatísticas)
        │  Celery (RabbitMQ broker, Redis result backend)
        ▼
Microsserviços FastAPI (microservices/)
  ├─ document-generator  (relatórios PDF, exportação .apkg — já implementado)
  ├─ ai-agent            (LangChain/LangGraph — Sprint 5)
  └─ whatsapp-evolution   (Evolution API — Sprint 6)
```

Estrutura de pastas: cada unidade implantável é uma pasta própria na raiz — `django/` (o backend principal), `microservices/<nome>/` (cada microsserviço FastAPI, um por pasta) e `frontend/` (SPA React, Sprint 3). `docker-compose.yml` e `Makefile` ficam na raiz e orquestram todas elas.

- **Backend principal**: Django + DRF, multi-tenant, URLs versionadas (`/api/v1/`).
- **Domínio de deck/card**: `django/apps/decks/` — entities, value objects e repositórios Mongo (via Motor), consolidados a partir do protótipo anterior.
- **Microsserviço de documentos**: `microservices/document-generator/` — FastAPI, gera `.apkg` (genanki + gTTS) e relatórios PDF.
- **Mensageria**: RabbitMQ (broker do Celery) + Redis (result backend/cache).
- **Deploy real**: VPS (Docker Compose) — não AWS. O único uso de AWS é o bucket S3 do frontend estático.
- **Observabilidade**: logs estruturados → Prometheus/Grafana → node_exporter → exporter RabbitMQ/Celery (ordem de instrumentação já decidida, ver PROMPT_REFINADO.md).

## 🛠️ Stack

| Camada | Tecnologia |
|---|---|
| Backend principal | Django 6 + Django REST Framework, Python 3.13, Poetry |
| Microsserviços | FastAPI, `venv`/`requirements.txt` por serviço |
| Banco relacional | PostgreSQL (auth/permissions do Django) |
| Banco de domínio | MongoDB (decks/cards/estatísticas), via Motor |
| Fila/assíncrono | Celery + RabbitMQ + Redis |
| Frontend | React (SPA estática, hospedada em S3) |
| Deploy | Docker Compose numa VPS |

## 🚀 Como rodar localmente

### Pré-requisitos
- Python 3.13 (via `pyenv`, já pinado em `.python-version`)
- Poetry
- Docker + Docker Compose

### Passo a passo

1. **Instale as dependências do Django**
   ```bash
   poetry -C django install
   ```

2. **Configure as variáveis de ambiente**
   ```bash
   cp django/config.example.env django/.env
   cp microservices/document-generator/config.example.env microservices/document-generator/.env
   ```
   Gere uma `DJANGO_SECRET_KEY` real e coloque no `django/.env`:
   ```bash
   poetry -C django run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

3. **Suba a stack completa** (Django, Postgres, MongoDB, Redis, RabbitMQ, Celery worker, document-generator)
   ```bash
   make up
   ```
   Django fica em `http://localhost:8000`, o document-generator em `http://localhost:8001`.

4. **Rode as migrations** (o container `web` já roda `migrate` automaticamente no entrypoint; para rodar manualmente fora do container)
   ```bash
   make migrate
   ```

5. **Health checks**
   ```bash
   curl http://localhost:8000/api/v1/health/
   curl http://localhost:8001/document-generator/v1/health/
   ```

### Comandos úteis (`Makefile`)

| Comando | O que faz |
|---|---|
| `make up` / `make down` | Sobe/derruba a stack via Docker Compose |
| `make logs` | Segue os logs de todos os serviços |
| `make migrate` / `make makemigrations` | Migrations do Django |
| `make run` | Roda o Django fora de container (`runserver`) |

## 🧪 Testes

```bash
# Teste de integração MongoDB (requer `make up` rodando, ao menos o serviço mongo)
poetry -C django run python -m apps.decks.tests.test_mongodb_integration
```

## 🎯 Roadmap

Roadmap completo, em sprints, com checklist detalhado: **[PRD.md](./PRD.md)**.

- [x] Sprint 0 — Fundação de arquitetura (Django + domínio consolidado + Docker Compose + microsserviço de documentos)
- [ ] Sprint 1 — Autenticação & multi-tenant
- [ ] Sprint 2 — Decks & Cards (domínio core)
- [ ] Sprint 3 — Frontend base & home dashboard
- [ ] Sprint 4 — Exportação Anki & microsserviço de documentos (integração completa)
- [ ] Sprint 5 — Agente de IA (LangChain/LangGraph)
- [ ] Sprint 6 — Notificações WhatsApp (Evolution API)
- [ ] Sprint 7 — Relatório semanal por e-mail
- [ ] Sprint 8 — Deploy real (VPS + S3 + domínio)
- [ ] Sprint 9 — Observabilidade
- [ ] Sprint 10 — Hardening & revisão final

## 🤝 Contribuindo

Este é um projeto de portfólio/estudo. Sinta-se à vontade para sugerir melhorias ou reportar issues.

## 📝 Licença

Este projeto é de uso pessoal/educacional.

## 👤 Autor

**Willames Campos**
- Email: willwjccampos@gmail.com

---

**Desenvolvido com foco em arquitetura orientada a eventos, multi-tenant e aprendizado guiado de cloud/DevOps.**
