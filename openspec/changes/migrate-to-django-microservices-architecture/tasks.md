## 1. System design (mentored)

- [x] 1.1 Invocar a skill `backend-mentor` para conduzir, de forma didática, o desenho do system design da arquitetura-alvo (Django + microsserviços FastAPI + MongoDB + mensageria)
- [x] 1.2 Registrar o diagrama de componentes e o fluxo de dados resultante (ver `design.md`, decisões D1–D12)
- [x] 1.3 Definir o banco relacional do Django para `auth`/`Permission`/`Group` — **decidido**: PostgreSQL, containerizado localmente também (D3 em `design.md`)
- [x] 1.4 Confirmar a ordem dos microsserviços FastAPI — **decidido**: documentos → agente de IA → WhatsApp/Evolution API
- [x] 1.5 Registrar a meta de escala (10.000 usuários ativos com requests esporádicos, não conexões persistentes simultâneas) como objetivo de design — Django deve permanecer stateless; infraestrutura não é provisionada para essa meta agora (D9 em `design.md`)

## 2. Fundação Django

- [x] 2.1 Criar o projeto Django `core` na raiz, com `apps/` para as futuras apps de produto
- [x] 2.2 Configurar settings segregados por ambiente (local vs. produção), com `python-dotenv`/`load_dotenv()` na inicialização
- [x] 2.3 Configurar `DJANGO_SECRET_KEY` via variável de ambiente, populando `.env`/`config.example.env`
- [x] 2.4 Configurar versionamento de URLs (`/api/v1/...`) e o banco relacional PostgreSQL (decidido na tarefa 1.3)
- [x] 2.5 Validar que `python manage.py runserver` sobe sem erros com um endpoint mínimo (ex.: health check) — validado tanto local quanto containerizado, com Postgres real
- [x] 2.6 Registrar a taxa de rate limiting — 10 req/s por usuário/cliente, atualizada na Sprint 7 (D12 em `design.md`) — e o lembrete de revisitar idempotência das operações com retry

## 3. Consolidação do domínio

- [x] 3.1 Mapear, a partir de `legacy/domain/entities` e `legacy/infrastructure`, quais entidades/value objects/repositórios serão migrados (Card, Deck, GenerationSession)
- [x] 3.2 Criar a primeira app Django de domínio (ex.: `apps/decks/`) e migrar as entidades/value objects para dentro dela
- [x] 3.3 Migrar os repositórios Mongo (`CardRepository`, `DeckRepository`, `GenerationSessionRepository`) via Motor, adaptados ao padrão da nova app — validado end-to-end via `apps/decks/tests/test_mongodb_integration.py`, incluindo a correção de um bug real de conversão `ObjectId ↔ UUID` que impedia save/find de funcionar
- [x] 3.4 Portar/atualizar `test_mongodb_integration.py` para rodar a partir da raiz do projeto, sem depender de `legacy/` no path
- [x] 3.5 Integrar a lógica de geração de card/áudio/exportação `.apkg` (`generator_v2.py`) ao serviço de domínio ou ao microsserviço de documentos (ver tarefa 5) — validado gerando um `.apkg` real via `POST /decks/export`
- [x] 3.6 Descartar a estrutura de domínio antiga (`legacy/domain/models.py`, `legacy/services/anki_deck_generator/`) após a migração validada

## 4. Ambiente de desenvolvimento local

- [x] 4.1 Criar `docker-compose.yml` na raiz subindo Django, PostgreSQL (auth do Django), MongoDB (deck/card/stats), Redis e RabbitMQ
- [x] 4.2 Configurar containers non-root com script `entrypoint`, seguindo a regra já definida em `PROMPT_REFINADO.md` — verificado via `whoami`/`id` dentro dos containers
- [x] 4.3 Corrigir o `Makefile`: reapontar o alvo Postgres (hoje órfão, não usado por nenhum código) para servir de fato o Django, adicionar alvos para subir a stack completa e rodar migrations do Django
- [x] 4.4 Unificar dependências: `pyproject.toml`/Poetry para o Django, `venv`/`requirements.txt` por microsserviço FastAPI, eliminando divergência entre arquivos
- [x] 4.5 Validar que `make up` (ou equivalente) sobe a stack completa localmente sem erros

## 5. Reclassificação do FastAPI como microsserviço satélite

- [x] 5.1 Mover `presentation/api/` (e o app factory de `main.py`) para um diretório de microsserviço dedicado (ex.: `microservices/document-generator/`)
- [x] 5.2 Validar que o serviço sobe e responde de forma independente do processo Django
- [x] 5.3 Documentar o contrato de comunicação Django → microsserviço de documentos (payload de entrada, resposta, autenticação de serviço-a-serviço) — contrato de payload documentado via os schemas Pydantic em `microservices/document-generator/app/routes/decks.py`; autenticação serviço-a-serviço fica para a Sprint 4 (quando o Django efetivamente chamar este endpoint)
- [x] 5.4 Adicionar Celery + RabbitMQ (broker) + Redis (result backend/cache) à stack (task list de publicação de eventos fica para a change de mensageria — aqui só a infraestrutura base)

## 6. Fundação de deploy real (VPS + S3) e observabilidade (mentorada)

- [x] 6.1 Invocar a skill `backend-mentor` para explicar, de forma guiada, as opções de deploy (VPS vs. AWS gerenciado) — **decidido**: deploy real em VPS, AWS restrita a S3 para o frontend
- [x] 6.2a Decidir o provedor de VPS — **decidido**: Hostinger (confirmar preço de renovação, não só o promocional, antes de contratar)
- [x] 6.2b Decidir como orquestrar os containers na VPS Hostinger — **decidido**: `docker compose` direto via SSH/script; Kubernetes explicitamente descartado para o deploy real (ver D11 em `design.md` e grupo 7 abaixo)
- [ ] 6.3 Configurar `docker-compose.yml` de produção e o processo de deploy (SSH + compose) para a Hostinger
- [ ] 6.4 Configurar o bucket S3 de hospedagem estática do frontend React e o pipeline de build/upload (ex.: GitHub Actions fazendo `npm run build` + sync para o S3)
- [x] 6.5 Registrar a decisão de domínio (registrador: Cloudflare) em `PROMPT_REFINADO.md`; compra efetiva do domínio fica sem data definida, sem pressa
- [x] 6.6 Invocar a skill `backend-mentor` para explicar, de forma guiada, o que instrumentar primeiro — **decidido**: (1) logs estruturados JSON com `request_id`, (2) `django-prometheus`/equivalente FastAPI, (3) `node_exporter`, (4) exporter RabbitMQ/Celery (fila + DLQ) — ver D10 em `design.md`
- [ ] 6.7 Adicionar logs estruturados + Prometheus (métricas da tarefa 6.6) + Grafana ao `docker-compose.yml` local
- [ ] 6.8 Decidir, via `backend-mentor`, quais dashboards Grafana montar primeiro e a política de alertas (o que exige ação humana imediata)

## 7. Terraform + AWS e Kubernetes (projetos de estudo separados — não bloqueiam esta change)

- [ ] 7.1 Quando o usuário decidir focar em estudar Terraform, criar um projeto simples e isolado (não este sistema) para praticar `terraform init/plan/apply/destroy`
- [ ] 7.2 Começar pelo state backend (bucket S3 + tabela DynamoDB de lock) e um único recurso de compute mínimo (ex.: EC2 `t4g.micro` free tier), evitando VPC customizada, NAT Gateway e recursos always-on caros
- [ ] 7.3 Revisitar, só depois de confortável com Terraform, se faz sentido migrar o deploy real deste sistema de VPS para AWS — decisão explicitamente adiada, não assumida
- [ ] 7.4 Quando o usuário decidir retomar o assunto (usuário sem experiência prévia — primeiro contato com a ferramenta), invocar `backend-mentor` para desenhar um roteiro de aprendizado de Kubernetes do zero (o que é um Pod, Deployment, Service, ConfigMap/Secret, Ingress)
- [ ] 7.5 Praticar localmente com `kind` ou `minikube` (sem custo, sem risco ao sistema real) antes de considerar qualquer cluster com IP público
- [ ] 7.6 Só depois de confortável com os conceitos, avaliar (com o usuário) se vale migrar algum workload de estudo para uma VPS pequena e descartável dedicada a isso — nunca a VPS Hostinger de produção deste sistema

## 8. Limpeza e documentação

- [x] 8.1 Remover o diretório `legacy/` após confirmar que todo conteúdo reaproveitável foi migrado
- [x] 8.2 Atualizar `README.md` (reescrito para a nova arquitetura) e `ETAPAS_PROJETO.md` (marcado obsoleto, aponta para `PROMPT_REFINADO.md`/`PRD.md`)
- [x] 8.3 Atualizar `PROMPT_REFINADO.md` com os gaps identificados neste levantamento e as decisões tomadas durante a execução desta change
- [x] 8.4 Registrar entrada no arquivo de changelog do projeto (`CHANGELOG.md`, criado nesta sprint), conforme já exigido em `PROMPT_REFINADO.md`
- [x] 8.5 Reorganizar a raiz do monorepo em pastas por unidade implantável — `django/` (backend, antes espalhado na raiz), `microservices/<nome>/` (renomeado de `services/`, evita colisão com `apps/decks/domain/services/`), `frontend/` (placeholder Sprint 3); `docker-compose.yml`/`Makefile` atualizados (ver `<estrutura_monorepo>` em `PROMPT_REFINADO.md`)
