# Changelog

Todas as alterações relevantes do projeto são registradas aqui, conforme `<regra_obrigatoria id="changelog">` em [PROMPT_REFINADO.md](./PROMPT_REFINADO.md).

## [Infraestrutura] Commit do `django/poetry.lock` — 2026-09-08

Fora do ciclo de sprints: bug descoberto ao cortar o primeiro release real (`v0.1.0`) com o `release.yml` da entrada seguinte — `django/poetry.lock` estava no `.gitignore` desde o commit inicial do projeto, então o build Docker em CI (`COPY pyproject.toml poetry.lock ./`) falhava com o arquivo ausente, apesar de existir e funcionar localmente. `poetry install` no `backend-test` do `ci.yml` também rodava sem lock, resolvendo dependências transitivas do zero a cada execução, sem trava de reprodutibilidade — não travava a suíte só porque nenhuma mudança de dependência causou conflito ainda.

### Corrigido
- `django/poetry.lock` removido do `.gitignore` e commitado — prática recomendada pelo próprio Poetry para aplicações (diferente de bibliotecas), garantindo que dev local, CI e build de imagem Docker resolvam exatamente as mesmas versões transitivas.

### Validado
- `docker build ./django` e `docker build ./microservices/document-generator` rodados localmente com sucesso após o commit do lockfile.

## [Infraestrutura] Versionamento SemVer via tag Git + release de imagens no GHCR — 2026-09-08

Fora do ciclo de sprints: fecha a regra mandatória `cicd` (`PROMPT_REFINADO.md`) — "DEVE existir um fluxo de deploy baseado em tags, via GitHub Actions". Complementa o [[changelog-check]] da entrada anterior: agora o próprio `make patch/minor/major` recusa taguear se o `CHANGELOG.md` não mudou desde a última tag.

### Adicionado
- `make patch` / `make minor` / `make major`: calculam a próxima versão a partir da última tag `vX.Y.Z` (via `git describe`), criam uma tag anotada e dão push — com três guardas antes de taguear: working tree limpa, HEAD sincronizado com `origin/main`, e `CHANGELOG.md` alterado desde a última tag (primeiro release, sem tag anterior, pula essa última checagem).
- `.github/workflows/release.yml`: disparado por push de tag `v*.*.*`, builda e publica no GHCR as duas imagens do projeto (`anki-generator-web` a partir de `django/`, `anki-generator-document-generator` a partir de `microservices/document-generator/`) com tags `vX.Y.Z` e `latest`, gravando versão e SHA do commit como labels OCI na própria imagem.
- Documentação dos novos comandos `make` no `README.md`.

### Alterado
- Nenhum arquivo de aplicação — mudança isolada em tooling de release.

### Fora de escopo (decisão explícita)
- Versionamento independente por serviço (django vs. document-generator) — optou-se por uma versão global única do projeto, coerente com este próprio `CHANGELOG.md` ser por projeto, não por serviço.
- Consumir essas imagens versionadas no deploy real da VPS (troca de `docker compose build` local por `docker compose pull` de uma tag fixa do GHCR) — fica para o Sprint 15 (Deploy real).
- Corte do primeiro release (`v0.0.1`) — esta entrada só adiciona a ferramenta; a decisão de quando cortar a primeira tag fica para depois do merge.

## [Infraestrutura] Gate de CHANGELOG obrigatório em PRs — 2026-09-08

Fora do ciclo de sprints: mentoria sobre versionamento (SemVer, tags Git, imagens Docker) identificou que a regra mandatória `changelog` era só verificada de olho, sem gate — nada impedia um PR de mexer em código sem tocar no `CHANGELOG.md`. Este é o primeiro passo (shift-left do próprio gate de CI) antes de construir a automação de tags/release que atende à regra mandatória `cicd`.

### Adicionado
- Job `changelog-check` em `.github/workflows/ci.yml`: falha o PR se ele alterar qualquer arquivo fora de uma lista de exceção (documentação/planejamento: `docs/`, `openspec/`, `.claude/`, `.vscode/`, `README.md`, `PRD.md`, `PROMPT_BRUTO.md`, `PROMPT_REFINADO.md`, `ETAPAS_PROJETO.md`) sem também alterar `CHANGELOG.md`. Roda só em `pull_request`, comparando via merge-base (`origin/<base>...HEAD`) contra a branch de destino — não repete a checagem no `push` pós-merge.
- Lista de exceção é uma denylist (o que NÃO exige changelog), não allowlist — decisão deliberada para que pastas/serviços novos criados no futuro fiquem cobertos pelo gate por padrão, em vez de exigir atualizar o regex toda vez.

### Alterado
- Branch protection da branch `main` no GitHub: passa a exigir PR antes de merge (sem exigência de aprovação de revisor — mantenedor único), os checks `lint`/`backend-test`/`frontend-test` obrigatórios, branch atualizada com `main` antes de mergear (`strict: true`), com bypass de admin mantido (`enforce_admins: false`) para emergências.

### Fora de escopo (decisão explícita)
- `changelog-check` ainda não é um check obrigatório na branch protection — só passa a ser exigido depois de rodar pelo menos uma vez de verdade nesta própria PR, evitando travar merges futuros esperando um status que nunca é reportado.
- Automação `make major/minor/patch` (bump de versão via tag Git anotada) e o workflow de release que builda/publica as imagens Docker no GHCR (atendendo à regra mandatória `cicd`) ficam para uma etapa seguinte.

## [Sprint 8] Pipeline de Testes & CI/CD — 2026-09-07

Nenhuma sprint até aqui (0-7) foi mesclada na `main` com gate automatizado — os testes existentes só rodavam se alguém lembrasse de rodar localmente antes do merge. Antecipada pro lugar da antiga Sprint 10 por decisão explícita do usuário. Fecha também a regra mandatória `ferramentas-lint` (`PROMPT_REFINADO.md`), nunca implementada: o backend não tinha `black` nem `pre-commit` configurados. Ver `openspec/changes/sprint-8-pipeline-ci-cd/`.

### Adicionado
- `.github/workflows/ci.yml`: workflow único do GitHub Actions com 3 jobs independentes (`lint`, `backend-test`, `frontend-test`), disparado tanto em `pull_request` (visando `main`) quanto em `push` (`main`, pós-merge) — mesma suíte nos dois gatilhos.
- Job `backend-test` roda `pytest apps/` contra Postgres, MongoDB e Redis como service containers do próprio job (mesmas imagens do `docker-compose.yml`), não mocks.
- `black` como dependência de dev do Django (`django/pyproject.toml`), com `[tool.black]` configurado.
- `.pre-commit-config.yaml` na raiz do repo, com o hook oficial do `black` restrito a `django/`.
- Badge de status do CI no `README.md`.

### Alterado
- Reformatação única de 54 arquivos Python existentes via `black .`, aplicada antes de ativar o gate `black --check` no CI (comportamento e testes inalterados — só formatação).
- `[tool.black]` (`django/pyproject.toml`) usa `force-exclude` pra nunca tocar `manage.py` nem `**/migrations/*.py` — arquivos gerados pelo próprio Django, não código de aplicação escrito à mão. `force-exclude` (não `exclude`) é necessário pra a exclusão valer também quando o `pre-commit` chama o `black` com a lista explícita de arquivos alterados, não só no `black --check .` do CI.

### Fora de escopo (decisão explícita)
- Ampliar a cobertura de testes existente (a pipeline roda o que já existe; cobertura cresce organicamente a cada sprint futura).
- CD de verdade (deploy automatizado a partir do merge em `main`) — decisão de como o deploy pra VPS acontece fica pra Sprint 15.
- `ruff`/`flake8` além do `black` — não pedido pela regra mandatória.

### Validado
- `pytest apps/`: 68 testes, 0 falhas, após a reformatação via `black`.
- `black --check .`: 92 arquivos verificados (`manage.py` e `**/migrations/*.py` fora do escopo do formatador), 0 divergências.
- `npm test`: 10 arquivos, 35 testes, 0 falhas (frontend não foi alterado nesta sprint).
- `npm run lint`: 0 erros e 0 warnings.

## [Sprint 7] Gerenciamento de Decks & Cards (Frontend) — 2026-08-29

Fecha o ciclo de gerenciamento que até agora só existia na API: usuários autenticados passam a listar, criar, editar e excluir decks e cards pela SPA. Ver `openspec/changes/sprint-7-gerenciamento-deck-card-frontend/`.

### Adicionado
- Tela `/decks` com listagem dos decks do usuário, cards de acesso ao detalhe e estado vazio com CTA de criação.
- Tela `/decks/novo` com formulário de título, descrição, categoria e `daily_review_goal`; após a criação, navega para o detalhe do novo deck.
- Tela `/decks/:deckId` com dados e edição inline do deck, contagem mínima de cards e botão "Ver todos os cards", sem baixar a coleção completa.
- Tela dedicada `/decks/:deckId/cards` com lista, estado vazio e criação/edição/exclusão de cards.
- `GET /api/v1/cards/count/?deck_id=...`, que executa `count_documents` escopado por `owner_id`/soft delete e retorna somente `{ "count": N }`.
- Ponte assíncrona persistente por processo para as chamadas DRF síncrono → Motor, com inicialização da conexão protegida contra concorrência.
- Comando idempotente `migrate_card_fields` para migrar documentos Mongo existentes e substituir índices baseados nos paths antigos.
- Criação inline de categoria a partir do seletor nativo do formulário de deck; a categoria recém-criada é selecionada automaticamente.
- `ConfirmDialog` compartilhado para deck e card, composto com `Card`/`Button` e aviso explícito da janela de retenção de 7 dias.
- Mutations dos clientes de API: `create`/`update`/`delete` para decks e cards, mais `fetchCategories`/`createCategory`.
- Testes Vitest + React Testing Library para contratos de API, contagem no detalhe, navegação dedicada, confirmação de exclusão, estados vazios, CRUD de deck/card, categoria inline e estatísticas do último deck na Home.

### Alterado
- `App.jsx`: o placeholder de `/decks` foi substituído por quatro rotas reais de gerenciamento, incluindo `/decks/:deckId/cards`.
- O contrato de Card foi renomeado em todo o monorepo para `front`, `back`, `front_description` e `back_description`, incluindo domínio, Mongo, API Django, SPA, seed e document-generator; os rótulos visíveis permanecem em português.
- O gráfico da Home deixou de somar a página recente de revisões de todos os decks e agora consome `rating_distribution` do último deck estudado pelo mesmo endpoint usado no detalhe.
- Rate limit global de usuário/anônimo ampliado de 3 para 10 req/s por decisão explícita do usuário; a 11ª chamada dentro da janela continua recebendo `429`.
- `Button` aceita um componente de renderização alternativo para que links mantenham o mesmo padrão visual sem aninhar elementos interativos; `Input` também atende `textarea` com o mesmo estilo auditado.
- Tokens visuais ganharam `overlay` e `letterSpacingUpper`, ambos rastreados diretamente ao `design_system/design-system.html` em `tokens/AUDIT.md`.

### Validado
- `pytest apps/`: 68 testes, 0 falhas — inclui contagem mínima, soft delete, isolamento, migração idempotente, limite 10/11, estatísticas por deck e detalhe+contagem concorrentes.
- `npm test`: 10 arquivos, 35 testes, 0 falhas.
- `npm run lint`: 0 erros e 0 warnings.
- `npm run build`: build de produção concluído.
- `document-generator`: 10 testes, 0 falhas com o payload e o modelo Anki renomeados.
- HTTP real: duas leituras de detalhe + duas contagens simultâneas retornaram `200`; burst retornou 10× `200` e a 11ª `429`; resposta de contagem confirmada como apenas `{ "count": 4 }`.

## [Sprint 6] Ciclo de Vida de Deck/Card — 2026-08-27

Fecha o gap de "só existe create/read completo" — Deck/Card/Category ganham exclusão com retenção de 7 dias (soft delete, não delete físico direto), edição completa via PATCH e meta de estudo persistida por deck. Resolve de vez o gap de cascade delete de `CardReview`, aberto desde a Sprint 3 (`PRD.md` §7.1). Ver `openspec/changes/sprint-6-ciclo-de-vida-deck-card/`.

### Adicionado
- `deleted_at: Optional[datetime]` em `Deck`, `Card` e `Category` — soft delete via timestamp, não um booleano, permite calcular a janela de retenção de 7 dias diretamente.
- Helper único de filtro (`schemas.base_filter`) usado por todo método de leitura das três entidades — inclui `find_by_front`/`find_similar_cards`/`find_duplicates`/`exists_by_front` (nomes atualizados na Sprint 7).
- `DELETE /api/v1/decks/{deck_id}/` cascateia soft delete pros cards do deck; `DELETE /api/v1/cards/{card_id}/` soft-deleta individualmente; `DELETE /api/v1/categories/{category_id}/` soft-deleta a categoria e **desvincula** (não cascateia) os decks que a referenciam (`category_id → None`) — categoria é rótulo organizacional opcional, diferente da relação obrigatória Card→Deck.
- `apps/decks/tasks.py` (`purge_soft_deleted`) — primeira task Celery real do projeto, registrada em `CELERY_BEAT_SCHEDULE`, remove fisicamente registros soft-deletados há mais de 7 dias nas três entidades.
- Serviço `celery-beat` no `docker-compose.yml` — gap encontrado depois do primeiro "pronto": `CELERY_BEAT_SCHEDULE` sozinho não agenda nada, precisa de um processo `celery beat` rodando pra disparar a task na hora certa (só existia `celery-worker`, que apenas consome fila). Volume nomeado `celery_beat_data:/var/lib/celery` (mesmo padrão do `document_generator_audio`) — `--schedule` fora de `/app` porque o bind mount de dev sobrescreve o `chown` da imagem, e o usuário não-root não conseguia escrever o arquivo de estado do scheduler ali.
- `purge-soft-deleted-daily` migrado de `timedelta(days=1)` pra `crontab(hour=0, minute=0)` — horário fixo (meia-noite), não "24h depois de o `celery-beat` ter iniciado" (que dependeria de quando o container subiu/reiniciou pela última vez). `CELERY_TIMEZONE = "America/Sao_Paulo"` (novo) — meia-noite de Brasília, não UTC; `TIME_ZONE` do Django continua UTC (grava tudo em UTC no banco), só o agendamento do Celery respeita o fuso local.
- `daily_review_goal: Optional[int]` em `Deck`, editável via `PATCH` — substitui a meta de estudo client-side/global da Sprint 3.
- `apiFetch` (frontend) trata `403` distintamente de outros erros, com mensagem de permissão clara em vez do erro técnico genérico — `HomePage.jsx` já reflete isso na única tela que hoje renderiza erro de fetch.

### Alterado
- `DeckRepository.delete()`/`CardRepository.delete()`/`CategoryRepository.delete()` passam de delete físico pra soft delete; `update()` de cada repositório passa a exigir `deleted_at: None` no filtro (não é possível editar um registro já soft-deletado por essa via).
- `DeckRepository.delete()` deixou de cascatear delete físico em `GenerationSessionRepository` — com o soft delete, apagar fisicamente uma entidade satélite na hora não faz mais sentido (contradiria a janela de retenção); `GenerationSession` é código morto do protótipo antigo de geração via IA, sem nenhum caminho de criação no produto atual, então isso não tem efeito observável hoje.

### Removido
- `DeckRepository.find_by_user_id`/`count_by_user_id` — código morto achado numa auditoria pré-sprint (duplicavam `find_all`/`count`, nenhum call-site em view/teste/seed).

### Validado
- `pytest apps/`: 53/53 testes passando, incluindo os 10 novos de `test_soft_delete_lifecycle.py` (soft delete, cascade, desvínculo, purge com timestamp forjado, `CardReview` sobrevivendo à exclusão, PATCH imune a `owner_id`/`created_by`/`updated_by` no payload) e os das Sprints 1–5 (nada quebrou).
- `celery-beat` sobe sem erro de permissão, `celery-worker` registra `apps.decks.tasks.purge_soft_deleted`; disparo real via `.delay()` percorrendo RabbitMQ → worker → Mongo confirmado nos logs (`succeeded in 0.02s`).
- `CELERY_TIMEZONE` confirmado nos logs reais do `celery-beat`: `"Reset: Timezone changed from 'UTC' to 'America/Sao_Paulo'"`. `app.conf.timezone`/`app.now()` conferidos via shell, próxima execução calculada batendo com meia-noite de Brasília.

## [Sprint 5] Fundações Transversais: Auditoria & Permissões — 2026-08-23

Fecha duas regras mandatórias declaradas desde a Sprint 0/1 mas nunca implementadas (`permissoes-django`, `auditoria`), e endurece a autenticação service-to-service entre Django e o microsserviço de documentos — item originalmente planejado pra Sprint 9, adiantado pra cá por ser o mesmo tema de hardening. Ver `openspec/changes/sprint-5-fundacoes-transversais/`.

### Adicionado
- `created_by`/`updated_by` em `Deck`, `Card`, `Category`, `CardReview` — preenchidos pelos serializers a partir da request autenticada, nunca aceitos como input do cliente (mesmo padrão de `owner_id`).
- Grupo `standard_user` (Django `Group` nativo), atribuído automaticamente a todo usuário via `post_save` signal (`apps/accounts/signals.py`) — cobre Google, seed (`get_or_create`) e um futuro cadastro por e-mail/senha com um único hook; data migration (`0002_standard_user_group.py`) cria o grupo e faz backfill de usuários já existentes.
- `HasAuthorizedGroup` (`apps/decks/permissions.py`) substitui `IsAuthenticated` puro nas 8 views de decks/cards/categories/reviews — usuário autenticado sem grupo autorizado recebe 403, distinto do 401 de não-autenticado.
- JWT de serviço (HS256) auto-assinado pelo Django (`core/service_auth.py`) e verificado localmente pelo `document-generator` (`app/auth.py`), sem round-trip/introspection — fecha o endpoint `POST /document-generator/v1/decks/export`, que estava sem autenticação nenhuma e com a porta publicada pro host. Rotação sem downtime via `kid` versionado (`SERVICE_JWT_KEYS`/`SERVICE_JWT_ACTIVE_KID`), chave separada do `SIMPLE_JWT`/`DJANGO_SECRET_KEY` de usuário.
- `core/service_clients.py` (`call_document_generator`) — cliente HTTP autenticado reutilizável, pronto pra Sprint 9 (integração Django→document-generator) importar sem reimplementar a assinatura do token.
- Fundação de testes do `document-generator` (FastAPI): `pytest` + `fastapi.testclient.TestClient`, 9 testes cobrindo a verificação do JWT de serviço (token ausente/expirado/`kid` desconhecido/`aud` errada/segredo errado, janela de rotação com duas chaves, rejeição após remoção da chave antiga).

### Validado
- `pytest apps/` (Django): 43/43 testes passando, incluindo os das Sprints 1–4 (nada quebrou com a permission class nova).
- `document-generator` (FastAPI): 9/9 testes passando.
- Verificação manual ponta a ponta via curl: login funcional inalterado; `GET /api/v1/decks/` retorna 200 pra usuário no grupo, 403 pra autenticado sem grupo, 401 sem autenticação; `POST /decks/export` do `document-generator` rejeita sem token (401) e aceita com JWT válido assinado pelo Django (200 + `.apkg` gerado); cenário de rotação completo simulado (duas chaves simultâneas → remoção da antiga → só a nova aceita).

## [Sprint 4] Robustecimento do Frontend — 2026-08-21

Fechamento das lacunas técnicas da primeira entrega da SPA. Ver `openspec/changes/sprint-4-robustecimento-frontend/`.

### Adicionado
- Fundação mínima de testes frontend com Vitest 4, React Testing Library, jest-dom e jsdom; scripts `npm test`/`npm run test:watch` e 6 testes cobrindo Error Boundary, responsividade da sidebar, preferência persistida e exportação PDF sob demanda.
- `ErrorBoundary` global com fallback alinhado aos componentes/tokens existentes, evitando tela branca em falhas não tratadas de renderização.
- Favicon PNG 192×192 derivado do mascote exibido no `README.md`, com composição simplificada para legibilidade em abas do navegador.
- CSS dedicado para `HomePage` e `LoginPage`, eliminando todos os atributos `style` das páginas/componentes.

### Alterado
- Exportação PDF extraída para `lib/exportPdf.js`; `jsPDF` agora usa `import()` dinâmico e sai do caminho crítico. Build de produção: chunk principal de 338 kB, `jspdf` de 391 kB e `html2canvas` de 202 kB, não comprimidos.
- Sidebar passa a recolher automaticamente em viewport de até 1024px quando não há escolha manual. A preferência do usuário continua persistida no `localStorage` e prevalece sobre o breakpoint.
- Home ganhou largura máxima, grid que não força overflow e área do gráfico adaptável; Login ganhou largura fluida com limite preservando a composição original.
- `useAuth` e o contexto base foram separados do `AuthProvider`, eliminando o warning de Fast Refresh e mantendo o lint limpo.
- Makefile e READMEs atualizados com o alvo `frontend-test` e o fluxo de qualidade da SPA.
- Vite atualizado para 6.4.3 e Vitest para 4.1.11; `npm audit` passou com 0 vulnerabilidades em dependências de produção e desenvolvimento.

### Validado
- `make frontend-test`: 3 arquivos, 6 testes, 0 falhas.
- `npm run lint`: 0 erros e 0 warnings.
- `npm run build`: build estático concluído e chunks de PDF separados do principal.
- Chrome headless em 1024×768: Login e Home inspecionadas; sidebar colapsada na Home e nenhuma quebra horizontal (`scrollWidth = viewportWidth = 1024`).

## [Sprint 3] Frontend Base & Home Dashboard — 2026-08-11

Primeira superfície visual do sistema. Ver `openspec/changes/sprint-3-frontend-base-home-dashboard/`.

### Adicionado
- `frontend/`: SPA React via Vite, `react-router` para navegação entre seções, camada de API client (`fetch` + hooks) apontando para `/api/v1/...` com anexação de JWT.
- Tokens de design (`frontend/src/tokens/`) extraídos por auditoria real de `refs/Ashley_files/style.css` (o CSS que `design_system/design-system.html` documenta — um template comercial de portfólio, não um design system de app) — cor, tipografia ("Outfit"), espaçamento, raio de borda, cada valor rastreável a uma linha do CSS original (`AUDIT.md`).
- Componentes base (`Sidebar`, `AppShell`, `Card`, `Button`) construídos do zero em React usando os tokens — não se importa o CSS do template diretamente.
- Tela Home: último deck estudado, meta de estudo + % alcançado (client-side), gráfico de distribuição de revisões por resultado (Chart.js/`react-chartjs-2`) e exportação desse gráfico para PDF (`jsPDF`, direto do canvas).
- Menu lateral (decks, categorias, relatórios, chat IA) — chat IA é só placeholder visual, sem chamada de API (agente real chega na Sprint 10).
- `GET /api/v1/reviews/` (backend) — histórico de `CardReview` do usuário autenticado, mais recentes primeiro; `CardReviewRepository.find_by_owner()` novo.
- Checklist de auditoria de consistência visual (`frontend/src/tokens/VISUAL_AUDIT.md`), executado contra o código real via grep — encontrou e corrigiu 2 desvios (espaçamento inline fora dos tokens em `HomePage.jsx`).
- `Makefile`: alvos `frontend-install`/`frontend-dev`/`frontend-build`/`frontend-lint`/`seed`.
- Tela de login (`/login`) com dois fluxos: e-mail/senha (`dj_rest_auth.views.LoginView`, novo em `apps/accounts/urls.py`) e Google OAuth2 (fluxo "token client" do Google Identity Services — não o botão "Sign In" mais novo, que devolve ID token em vez do `access_token` OAuth2 que o `GoogleOAuth2Adapter` do backend espera). Componente `Input` novo (`frontend/src/components/ui/`).
- Fluxo de refresh de token na SPA: `access` + `refresh` guardados no `localStorage`; em qualquer 401, `apiFetch` tenta renovar via `/auth/token/refresh/` (deduplicando chamadas concorrentes) antes de repetir a requisição original; só desloga (evento `auth:session-expired`) se o refresh também falhar. `AuthContext`/`useAuth()` novos.
- Botão de recolher/expandir a sidebar, estado persistido em `localStorage`.
- `seed_decks.py`: todo usuário seedado agora tem senha conhecida (`anki12345`, documentada em `frontend/README.md`) para permitir login e navegação autenticada de ponta a ponta sem depender de credenciais reais do Google.

### Corrigido (gap de escopo encontrado em implementação)
- A proposta original desta sprint previa "nenhum impacto no backend" — falso: a Sprint 2 persistia `CardReview` mas nunca expunha leitura via API, e a Home não tem como mostrar "último deck estudado"/gráfico de estatísticas sem esse histórico. Resolvido com o menor impacto possível: um método de repositório + uma Generic View reaproveitando tudo que a Sprint 2 já construiu, não um endpoint novo com lógica própria.
- **Corrigido também**: CORS nunca tinha sido configurado (`django-cors-headers` não era nem dependência) — a SPA (`:5173`) e a API (`:8000`) são origens diferentes, então o navegador bloqueava a SPA de ler qualquer resposta, mesmo com JWT válido. Adicionado, com `CORS_ALLOWED_ORIGINS` liberado só pra `localhost:5173` em dev e vazio por padrão (via env var) em produção.
- **Corrigido também**: `Deck.title` gerado pelo comando de seed usava um padrão genérico (`"Categoria — Deck N"`) sem servir como identificador amigável na Home — encontrado testando a Home de verdade, não em revisão de código. `seed_decks.py` agora gera título + descrição reais e variados por deck (`DECK_CATALOG`); a Home exibe `Deck.description` (campo já existente desde a Sprint 2, nunca populado) quando presente.
- **Corrigido também**: "último deck estudado" fazia `GET /cards/{id}/` seguido de `GET /decks/{id}/` (2 requests em cadeia) só pra descobrir o deck de uma revisão — combinado com o double-effect do React 18 StrictMode em dev (`GET /reviews/` disparado 2x), a cadeia completa de 4 requests estourava o throttle de 3 req/s, retornando 429 e travando o card em "Não foi possível carregar o deck". Corrigido denormalizando `deck_id` (referência estável, não um título — sem risco de ficar desatualizado) direto no `CardReview`, no momento da revisão — a SPA agora busca o deck em 1 request só.

### Alterado
- `SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]`: 15min (Sprint 1) → 1h — o fluxo de dev manual (sem tela de login, token colado no `localStorage`) tornava a duração curta original irritante de testar. Nenhum ajuste necessário no blocklist de refresh token: seu TTL no Redis já é calculado dinamicamente a partir do `exp` real de cada token, não um valor fixo espelhando `ACCESS_TOKEN_LIFETIME`.

### Corrigido (configuração do allauth para login por e-mail/senha)
- `ACCOUNT_LOGIN_METHODS` não estava setado — allauth 65.x, sem essa config, usa o default (login só por `username`), incompatível com o `LoginSerializer` do dj-rest-auth (que manda `{email, password}`) e com `User.USERNAME_FIELD = "email"`. Confirmado pelo erro real da API (`"Deve incluir 'username' e 'password'"`) e inspecionando `allauth.account.app_settings` diretamente. Corrigido com `ACCOUNT_LOGIN_METHODS = {"email"}`.
- `ACCOUNT_SIGNUP_FIELDS` setado inicialmente como dict (formato errado) — confirmado lendo o parser real do allauth (`SIGNUP_FIELDS`, que itera só as chaves de um dict, nunca encontra o sufixo `"*"`) que isso faz todo campo virar `required=False` silenciosamente. Formato correto é lista de strings (`["email*", "password1*", "password2*"]`).
- `seed_decks.py` deixava usuários seedados pré-existentes com senha efetivamente inutilizável: a condição original (`if created or not user.has_usable_password()`) nunca re-setava a senha em reruns, porque `Django.is_password_usable("")` retorna `True` (só checa o marcador `!` de `set_unusable_password()`, não string vazia). Corrigido setando a senha incondicionalmente a cada seed.

### Decisão de escopo
- "Meta de estudo" (tarefa 3.2) não tem nenhum modelo no backend — nunca foi definida em nenhum spec de produto o que uma meta significa (cards/dia? semana?). Em vez de inventar schema sem requisito real, fica em `localStorage` por enquanto (não persiste entre dispositivos) — decisão documentada explicitamente (D7 em `design.md`), não escondida.

### Pendências conhecidas
- Login funciona (e-mail/senha e Google), mas cadastro de conta nova e vínculo de conta (mesmo e-mail via Google e via senha) ainda não — levantamento de requisitos feito, decisão de escopo pendente (ver PRD.md 7.1).
- Bundle de produção (~720KB não comprimido no chunk principal, por causa de `jsPDF`+`html2canvas`+Chart.js) ainda sem code-splitting — aceitável no volume desta sprint, revisitar se o bundle crescer mais.

## [Sprint 2] Decks & Cards (domínio core) — 2026-08-10

Primeira feature real sobre o domínio de deck/card migrado na Sprint 0, agora multi-tenant e com repetição espaçada. Ver `openspec/changes/sprint-2-decks-cards/`.

### Adicionado
- Isolamento multi-tenant em MongoDB: `owner_id` obrigatório em toda assinatura de método de repositório (`Deck`/`Category`/`Card`/`CardReview`), embutido diretamente no filtro da query — mecanismo próprio da camada Motor, já que o `TenantOwnedModel` da Sprint 1 é ORM/Postgres-only.
- Entidade `Category` (nova — não existia no domínio migrado); `Deck` ganhou `category_id`, `Card` ganhou `tags` e os campos de agendamento FSRS (`stability`, `difficulty`, `due_at`, `fsrs_state`).
- Repetição espaçada via FSRS (pacote `fsrs`, o mesmo algoritmo do Anki real desde 2023) — `domain/services/scheduling_service.py`.
- Entidade `CardReview` — um documento por evento de revisão (mesma granularidade do `revlog` do Anki), deliberadamente distinta de `GenerationSession` (que continua representando só o job de geração de cards via IA).
- Endpoints REST versionados (`/api/v1/decks/`, `/categories/`, `/cards/`, `/cards/{id}/review/`) via Generic Views do DRF sobre repositório Motor — serializers `serializers.Serializer` manuais (não `ModelSerializer`), `get_queryset()` retornando lista já resolvida via `async_to_sync`; `APIView` dedicada para a ação de revisão (não é CRUD).
- Índices Mongo por `owner_id`/`deck_id`/`category_id`/`tags`/`due_at`, definidos em `IndexDefinitions` (`schemas.py`) — agora fonte única também para `MongoDBConnectionManager.create_indexes()` (antes havia uma segunda lista hardcoded e divergente).
- Comando de seed multi-tenant (`seed_decks`): múltiplos usuários, decks/categorias/cards com tags, `CardReview` com datas passadas/recentes/futuras — entrypoint `asyncio.run` com `asyncio.gather` para inserções concorrentes reais (sem bridge `async_to_sync`), protegido contra produção (`settings.DEBUG`), suporte a `--reset`.
- 16 novos testes automatizados (isolamento cross-tenant contra Mongo real, CRUD dos endpoints, revisão/agendamento FSRS, cards devidos, guarda de produção do seed) — **28/28 passando** com a Sprint 1.
- Hierarquia de exceções própria do projeto (`core/exceptions.py`): `AppError`, base abstrata (não instanciável diretamente — nem `ABC` sozinho bloqueia isso em subclasses de `Exception`, foi preciso um guard manual). Duas ramificações: `DomainValidationError` (substitui todo `ValueError` cru levantado por entidades/objetos de valor) e `InfrastructureError` → `RepositoryError`/`CardNotFoundError`/`DeckNotFoundError`/`CategoryNotFoundError`/`SessionNotFoundError`/`MongoNotConnectedError`/`MongoConfigError` (substitui os `RuntimeError`/`ValueError` da camada Mongo). Consolidado em `apps/decks/infrastructure/exceptions.py`, corrigindo de passagem um layering estranho: `RepositoryError` vivia dentro de `card_repository.py` e todo outro repositório importava dela como se fosse módulo compartilhado.

### Corrigido
- **Bug real de produção, descoberto via verificação end-to-end com requests HTTP reais (não só testes unitários)**: `AsyncIOMotorClient` fica preso ao event loop em que foi criado; `asgiref.sync.async_to_sync` cria um event loop novo a cada chamada bridged, sem loop "principal" já rodando na thread. O singleton `MongoDBConnectionManager` e o cache de `_collection` por instância de repositório quebravam com `RuntimeError: Event loop is closed` já na segunda/terceira chamada do processo. Corrigido: `is_connected()` agora valida o loop atual e força reconexão quando diverge; repositórios pararam de cachear `_collection` na instância.
- `GenerationSessionRepository.find_by_id()` (Sprint 0) chamava `CardRepository.find_by_deck_id()` sem `owner_id` — quebrado pela mudança acima; `owner_id` agora é parâmetro explícito também nesse método.
- **Segundo bug real, também de produção, encontrado em revisão pré-commit**: `datetime.utcnow()` (deprecated) foi trocado por `datetime.now(timezone.utc)` em todo `apps/decks/` — mas o mais importante foi o que essa troca revelou: Motor/pymongo devolvem datetime *naive* na leitura (mesmo quando o valor foi inserido como aware), então revisar o mesmo card uma segunda vez (com `due_at`/`last_reviewed_at` vindos do Mongo) quebrava com `TypeError: can't subtract offset-naive and offset-aware datetimes` dentro do `fsrs.Scheduler`. Corrigido na fronteira `schemas.py`: novo helper `datetime_from_mongo()` reanexa o offset UTC em toda leitura, usado nos cinco schemas. Validado revisando o mesmo card 3x seguidas via API real.

### Qualidade de código (revisão pré-commit)
- Espaço em branco no fim de linha removido de 16 arquivos em `apps/decks/` (domínio + infraestrutura, código herdado da Sprint 0 nunca revisado antes).
- `seed_decks.py` reescrito para legibilidade: os `asyncio.gather(*( ... for ... ))` aninhados de 3 níveis viraram "monta a lista de objetos" → "salva tudo concorrentemente" como dois passos nomeados e separados, sem custo de performance; números mágicos (`2` decks por categoria, `4` cards por deck) viraram constantes nomeadas.

### Decisão de escopo
- Métodos/serviços legados do protótipo antigo de geração de vocabulário (`find_by_word`, `find_similar_cards`, `find_duplicates`, `exists_by_word`, `duplicate_detection_service`, `card_quality_service`) — não usados por nenhuma view/URL, não previstos no PRD — foram mantidos e escopados por `owner_id`, por decisão explícita do usuário, para o caso do agente de IA (Sprint 10) reaproveitar essa lógica.

## [Sprint 1] Autenticação & Multi-tenant — 2026-08-05

Primeira feature real do sistema, sobre a fundação da Sprint 0. Ver `openspec/changes/sprint-1-autenticacao-multi-tenant/`.

### Adicionado
- App `django/apps/accounts/`: model de usuário customizado (`email` único, `USERNAME_FIELD = "email"`), reaproveitando `AbstractUser`.
- Autenticação JWT (`djangorestframework-simplejwt`) com refresh token revogável via blocklist no Redis — logout tem efeito imediato, sem esperar a expiração natural do token.
- Login via Google OAuth (`django-allauth` + `dj-rest-auth`), exposto como endpoint REST (`/api/v1/auth/google/`) devolvendo JWT em vez de página HTML — decisão mentorada, justificada pela SPA (Sprint 3) ficar em origem separada (S3) da API Django.
- Isolamento multi-tenant reutilizável: `TenantOwnedModel`/`TenantOwnedQuerySet` (`apps/accounts/tenancy.py`) — qualquer model futuro herda em vez de reimplementar o filtro por usuário dono. Confirmado que "multi-tenant" neste projeto = isolamento por usuário, sem entidade `Organization`/`Tenant` separada.
- `AuditMixin`/`AuditSerializerMixin` (`apps/accounts/audit.py`): `created_at/by`, `updated_at/by` preenchidos automaticamente a partir do usuário autenticado, ignorando qualquer valor enviado pelo cliente.
- Rate limiting de 3 req/s por usuário/cliente via throttle classes do DRF, usando o Redis já configurado.
- Primeira infraestrutura de testes automatizados do projeto: pytest + pytest-django, 12 testes cobrindo isolamento multi-tenant, auditoria, rate limiting, permissões e o ciclo completo de refresh/logout do JWT.

### Corrigido
- `AUTH_USER_MODEL` definido antes de qualquer migration real ter sido aplicada com dados reais — única janela seguras para essa troca (documentado em design.md desta sprint).

### Pendências conhecidas
- `GOOGLE_OAUTH_CLIENT_ID`/`GOOGLE_OAUTH_CLIENT_SECRET` ainda não configurados com credenciais reais (requer criar um projeto OAuth no Google Cloud Console) — o fluxo de login com Google em si não foi validado ponta a ponta com o Google de verdade; toda a mecânica de emissão/revogação de JWT foi validada de forma independente.

## [Sprint 0] Fundação de arquitetura — 2026-08-04

Migração do monólito FastAPI incompleto para a arquitetura-alvo (Django como backend principal + microsserviços FastAPI satélites), conforme `openspec/changes/migrate-to-django-microservices-architecture/`.

### Adicionado
- Projeto Django (`django/core/` + `django/apps/decks/`), Python 3.13, Django 6, DRF, settings segregadas por ambiente (`local`/`production`), `python-dotenv` + `DJANGO_SECRET_KEY` via variável de ambiente.
- Domínio de deck/card/geração (`apps/decks/domain/`) e repositórios MongoDB via Motor (`apps/decks/infrastructure/`), consolidados a partir do protótipo anterior — com correção de um bug real de conversão `ObjectId ↔ UUID` que impedia `save`/`find_by_id` de funcionar.
- Microsserviço FastAPI de geração de documentos (`microservices/document-generator/`), com exportação `.apkg` (genanki + gTTS) validada end-to-end via container.
- `docker-compose.yml` na raiz: Django, PostgreSQL, MongoDB, Redis, RabbitMQ, Celery worker e o microsserviço de documentos — todos os containers de aplicação rodando com usuário non-root dedicado e `entrypoint.sh`.
- Fundação Celery + RabbitMQ (broker) + Redis (result backend/cache), sem tasks reais ainda.
- URLs versionadas (`/api/v1/...`) com endpoint de health check.
- `PRD.md` com roadmap completo do projeto em sprints.
- `frontend/` (placeholder da Sprint 3, ainda sem código).

### Alterado
- **Reorganização do monorepo por unidade implantável** (ver `<estrutura_monorepo>` em `PROMPT_REFINADO.md`): o Django, que estava espalhado solto na raiz (`core/`, `apps/`, `manage.py`, `pyproject.toml`, `Dockerfile`), passou para `django/`; `services/` foi renomeado para `microservices/` (evita colisão de nome com `apps/decks/domain/services/`, que já significa "serviços de domínio" em DDD). `docker-compose.yml` e `Makefile` continuam na raiz, atualizados para os novos caminhos (`poetry -C django ...`).
- `Makefile`: removido o alvo Postgres órfão (subia um container não usado por nenhum código); novos alvos `up`/`down`/`logs`/`migrate`/`makemigrations`/`run`.
- `pyproject.toml`: dependências FastAPI-específicas (genanki, gTTS, fastapi, uvicorn, pydantic-settings, sqlalchemy não utilizada) removidas — agora vivem em `microservices/document-generator/requirements.txt`; Python `^3.13`.
- `test_mongodb_integration.py` portado para `apps/decks/tests/`, roda a partir da raiz do projeto sem depender de `legacy/` no path.

### Removido
- `legacy/`, `presentation/`, `shared/`, `main.py`, `generator_v2.py` (raiz) — conteúdo reaproveitável migrado; o restante era duplicado ou não utilizado.

### Corrigido
- Bug de conversão `ObjectId → UUID` (e vice-versa) em `CardRepository`/`DeckRepository`/`GenerationSessionRepository`: o código original tentava construir um `uuid.UUID` diretamente a partir do hex de 24 caracteres de um `ObjectId` (que precisa de 32), o que fazia `save`/`find_by_id` falharem sempre. Nunca havia sido validado funcionando antes desta sprint.
