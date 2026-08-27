## 1. Scaffold

- [x] 1.1 Criar `frontend/` como SPA React via Vite (substitui o placeholder atual)
- [x] 1.2 Instalar e configurar `react-router`
- [x] 1.3 Estrutura de pastas (components/, pages/, api/, tokens/, lib/)
- [x] 1.4 Camada de API client (`fetch` + hooks) apontando para `/api/v1/...`, com anexação do JWT
- [x] 1.5 Documentar em `frontend/README.md` como obter um JWT manualmente para testar localmente — mantido como alternativa opcional depois que o login real (grupo 9) foi implementado

## 2. Tokens de design

- [x] 2.1 Auditar `refs/Ashley_files/style.css` e catalogar cor/tipografia/espaçamento reais em uso — `frontend/src/tokens/AUDIT.md`
- [x] 2.2 Criar arquivo de tokens (paleta de cor, `font-family: "Outfit"`, escala de espaçamento) a partir da auditoria — `tokens.js`/`tokens.css`
- [x] 2.3 Componentes base usando os tokens: layout com sidebar, card, botão

## 3. Home dashboard

- [x] 3.1 Card de último deck estudado (consumindo API real, com estado vazio para usuário sem histórico)
- [x] 3.2 Meta de estudo + % alcançado — **nota**: sem endpoint de backend (não existia nenhum conceito de meta); implementado client-side via `localStorage`, decisão documentada em D7 de `design.md`
- [x] 3.3 Gráfico de estatísticas com Chart.js (`react-chartjs-2`), dados vindos da API — distribuição de ratings (again/hard/good/easy) a partir de `GET /api/v1/reviews/`
- [x] 3.4 Exportação do gráfico para PDF via `jsPDF`

## 4. Navegação

- [x] 4.1 Menu lateral: decks, categorias, relatórios, chat IA (placeholder sem chamada de API)
- [x] 4.2 Rotas via `react-router` para cada seção

## 5. Auditoria de consistência visual

- [x] 5.1 Checklist comparando cada tela implementada contra os tokens documentados — `frontend/src/tokens/VISUAL_AUDIT.md`
- [x] 5.2 Corrigir qualquer cor/fonte/espaçamento fora dos tokens encontrado na auditoria — 2 desvios encontrados e corrigidos em `HomePage.jsx` (valores de espaçamento inline substituídos por tokens)

## 6. Documentação

- [x] 6.1 Atualizar `PROMPT_REFINADO.md` (`<decisoes_resolvidas>`) com D1–D3 de `design.md` (tokens curados, Chart.js+jsPDF, fetch sem React Query)
- [x] 6.2 Atualizar `PRD.md` (Sprint 3) marcando as tarefas concluídas
- [x] 6.3 Atualizar `CHANGELOG.md` com a entrada `[Sprint 3]`
- [x] 6.4 Atualizar `README.md` (arquitetura, stack, roadmap) refletindo o frontend

## 7. Backend (gap encontrado em implementação, ver D6 em design.md)

- [x] 7.1 `CardReviewRepository.find_by_owner()` + `GET /api/v1/reviews/` (`CardReviewListView`), reaproveitando o padrão de Generic View já estabelecido na Sprint 2
- [x] 7.2 Validado via requests HTTP reais contra o Django rodando (não só leitura de código)

## 8. Correções encontradas testando a Home de verdade num navegador (não em revisão de código)

- [x] 8.1 CORS nunca configurado (`django-cors-headers` não era dependência) — SPA (`:5173`) e API (`:8000`) são origens diferentes, navegador bloqueava a leitura da resposta mesmo com JWT válido. Adicionado; `CORS_ALLOWED_ORIGINS` liberado só para `localhost:5173`/`127.0.0.1:5173` em dev, vazio por padrão (via env var) em produção. Validado com `curl -H "Origin: ..."` confirmando o header `access-control-allow-origin` na resposta.
- [x] 8.2 `useLastStudiedDeck` (HomePage) não distinguia "carregando" de "falhou" — qualquer erro na cadeia `reviews → card → deck` ficava mostrando "Carregando deck…" pra sempre, sem forma de diagnosticar. Adicionado estado de erro explícito + log no console + mensagem de erro amigável na UI.
- [x] 8.3 `Deck.title` gerado pelo seed usava um padrão genérico (`"Categoria — Deck N"`) — não servia como identificador amigável na Home. `seed_decks.py` passou a gerar título + descrição reais e variados por deck (`DECK_CATALOG`, 2 decks por categoria com conteúdo real); Home passou a exibir `Deck.description` (campo já existente desde a Sprint 2, nunca populado) quando presente. Sem mudança de schema — confirmado com o usuário antes de implementar.
- [x] 8.4 "Último deck estudado" fazia `GET /cards/{id}/` → `GET /decks/{id}/` (2 requests em cadeia) só pra descobrir o deck — combinado com o double-effect do StrictMode em dev (`GET /reviews/` 2x), a cadeia de 4 requests estourava o throttle de 3 req/s (429). Corrigido denormalizando `deck_id` (referência estável, não um título — sem risco de desatualização) direto em `CardReview` no momento da revisão (`CardReviewView.post()` e `seed_decks.py`); a SPA busca o deck em 1 request. Validado via `curl` (deck_id presente na resposta de `/reviews/`, deck buscável diretamente).

## 9. Login real + refresh de token (gap encontrado testando a Sprint 3, ver D9 em design.md)

- [x] 9.1 `/login` com Google OAuth2 "token client" (`google.accounts.oauth2.initTokenClient`) — depende de `GOOGLE_OAUTH_CLIENT_ID`/`SECRET` reais para validação ponta a ponta, ainda pendente
- [x] 9.2 `/login` com e-mail/senha (`dj_rest_auth.views.LoginView` em `/auth/login/`) — validado ponta a ponta via `curl` e via seed (`anki12345`), sem depender de credenciais externas
- [x] 9.3 Corrigido `ACCOUNT_LOGIN_METHODS`/`ACCOUNT_SIGNUP_FIELDS` (allauth) para o login por e-mail/senha funcionar com `USERNAME_FIELD = "email"` — dois bugs de configuração encontrados e corrigidos, ver design.md D9
- [x] 9.4 `seed_decks.py`: senha (`anki12345`) setada incondicionalmente em todo usuário seedado a cada run (bug anterior deixava usuários pré-existentes com senha "usável" mas vazia)
- [x] 9.5 Fluxo de refresh de token na SPA: `access`+`refresh` em `localStorage`, `apiFetch` renova via `/auth/token/refresh/` num 401 (deduplicando chamadas concorrentes) e repete a chamada original; `auth:session-expired` só dispara se o refresh também falhar
- [x] 9.6 Botão de recolher/expandir a sidebar (estado em `localStorage`) e botão "Sair" (logout)
- [x] 9.7 `pytest apps/accounts apps/decks` — 28/28 passando; `npm run build`/`npm run lint` — limpos (exceto o warning pré-existente de fast-refresh em `AuthContext.jsx`, aceito)
