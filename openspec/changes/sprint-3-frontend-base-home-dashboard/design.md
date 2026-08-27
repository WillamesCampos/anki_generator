## Context

`frontend/` é hoje só um placeholder (`README.md`) — nenhum código React existe. `design_system/design-system.html` (a fonte visual mandatória, per `PROMPT_REFINADO.md`) é uma página de documentação viva que referencia `refs/Ashley_files/style.css` (4229 linhas) como fonte real dos tokens — mas esse CSS não é um design system de aplicação: é o CSS compilado de "Ashley", um template comercial de portfólio/agência (jQuery + Bootstrap grid + GSAP + Swup + Swiper + Fancybox), pensado para hero sections, galeria de projetos e lightbox — não para sidebar de navegação, tabelas ou dashboard de estatísticas. Essa dissonância foi levantada e resolvida com o usuário antes deste documento (ver Decisions, D1).

O backend (Sprints 0–2) já expõe tudo que a Home precisa: `/api/v1/auth/...` (JWT), `/api/v1/decks/`, `/api/v1/cards/?due=true`, `/api/v1/cards/{id}/review/`. Sprint 3 é puramente consumidora dessa API — nenhum endpoint novo.

## Goals / Non-Goals

**Goals:**
- Scaffold da SPA React rodando localmente, com roteamento e uma camada fina de chamada à API do Django.
- Um arquivo de tokens de design (cor/tipografia/espaçamento) extraído de `refs/Ashley_files/style.css`, consumido por todos os componentes — nenhuma cor/fonte "inventada" fora dessa fonte.
- Tela Home funcional: último deck estudado, meta de estudo + % alcançado, gráfico de estatísticas consumindo a API real.
- Exportação do gráfico da Home para PDF.
- Menu lateral de navegação (decks, categorias, relatórios, chat IA como placeholder visual), recolhível.
- Checklist de auditoria de consistência visual contra os tokens extraídos.
- Tela de login (Google OAuth) + fluxo de refresh de token/tratamento de 401 — adicionado ao escopo em implementação (ver D9), não fazia parte do plano original desta sprint.

**Non-Goals:**
- Telas de CRUD de decks/cards/categorias em si (Sprint 4+) — Sprint 3 só precisa de dados suficientes pra Home renderizar algo real (pode ser a listagem que já existe via `GET /api/v1/decks/`).
- Chat com o agente de IA funcional — é só um item no menu lateral, sem tela/backend por trás (Sprint 6).
- React Query/SWR ou qualquer camada de cache de dados — decisão explícita (D3): `fetch` + hooks nativos, revisitado só se uma dor real de cache/revalidação aparecer nas sprints seguintes.
- Validação ponta a ponta do login com o Google real — depende de `GOOGLE_OAUTH_CLIENT_ID`/`SECRET` reais (Google Cloud Console), ainda não configurados (mesma pendência desde a Sprint 1). O fluxo é construído e testável assim que as credenciais existirem.
- Testes automatizados abrangentes do frontend (login, refresh, sidebar) — Sprint 8 (Testes & CI/CD); a Sprint 4 antecipa somente a fundação Vitest/RTL e a cobertura dos comportamentos críticos de robustecimento introduzidos nela.

## Decisions

### D1 — Tokens curados extraídos de `style.css`, componentes React construídos do zero
`refs/Ashley_files/style.css` não é uma biblioteca de componentes reaproveitável para um dashboard — é o CSS de um site de portfólio. A extração de tokens (tarefa 3.2 do PRD) significa: auditar `style.css` e produzir um arquivo de tokens próprio (paleta de cor, `font-family: "Outfit"`, escala de espaçamento) — confirmados por inspeção direta do CSS: cor de destaque `rgb(255, 152, 0)` (usada repetidamente como accent/hover/CTA), texto base `rgb(0, 0, 0)` sobre fundos claros (`rgb(242, 242, 242)`), fonte "Outfit" (Google Font, sans-serif). Componentes (sidebar, card de estatística, botão) são construídos nativamente em React usando esses tokens — não importamos `style.css`/`bootstrap-grid.css` diretamente.
- **Alternativa considerada**: importar `style.css` + `bootstrap-grid.css` direto e reusar as classes existentes. Rejeitada — traz ~4200 linhas de CSS de hero/galeria/lightbox irrelevantes para um dashboard, acopla o markup React a classes Bootstrap globais em vez de estilos escopados por componente, e viola o espírito da tarefa 3.2 ("extrair tokens", não "importar CSS inteiro").
- **Alternativa considerada**: recriar os componentes do zero, sem qualquer referência a `style.css` (design "inspirado", não extraído). Rejeitada — `PROMPT_REFINADO.md` é explícito: nenhuma cor/fonte/componente fora do design system é aceito (critério de aceite 12); os tokens têm que vir de uma auditoria real do CSS, não de memória/suposição.

### D2 — Gráfico e exportação PDF: Chart.js (`react-chartjs-2`) + `jsPDF`
Chart.js renderiza em `<canvas>`, então a exportação em PDF (tarefa 3.4) é direta: `canvas.toDataURL()` alimenta o `jsPDF` sem passo intermediário.
- **Alternativa considerada**: Recharts (SVG, API mais declarativa, popular em dashboards React). Rejeitada para este caso específico — exportar um gráfico SVG pra PDF exige convertê-lo pra canvas primeiro (via `html2canvas` ou similar), uma camada extra e menos confiável (fontes/gradientes podem sair diferentes na exportação). Como a exportação em PDF é um requisito explícito do PRD (não hipotético), a vantagem do Chart.js aqui é concreta, não teórica.

### D3 — Data fetching: `fetch` nativo + hooks React, sem React Query/SWR
Sprint 3 consome poucos endpoints (decks, cards devidos) em 1–2 telas. React Query resolveria cache/revalidação entre navegações — um problema que ainda não existe. Adicioná-lo agora seria complexidade sem dor medida, mesmo princípio YAGNI já aplicado no backend (ex.: D3 da Sprint 2, sobre não adotar `adrf` sem necessidade real).
- **Alternativa considerada**: adotar React Query desde já, para não migrar o padrão de data-fetching no meio do projeto. Rejeitada por ora — se as Sprints 4+ (mais telas, mais navegação entre elas) mostrarem necessidade real de cache/revalidação, essa é a hora de introduzir, com o requisito real na mão.

### D4 — Build tool: Vite
Create React App está descontinuado (não recebe mais atualizações oficiais). Vite é o padrão de fato atual para SPAs React — dev server rápido (HMR nativo via ESM), build de produção via Rollup, zero configuração exótica necessária para este escopo. Não há trade-off real a ponderar aqui (diferente de D1–D3), por isso não foi levado como pergunta ao usuário.

### D5 — Roteamento: `react-router`
O menu lateral (tarefa 3.5) implica múltiplas seções navegáveis (Home, decks, categorias, relatórios) — `react-router` é a biblioteca padrão do ecossistema para isso. Mesmo raciocínio de D4: escolha de baixa controvérsia, não é um trade-off genuíno para este escopo.

### D6 — `GET /api/v1/reviews/`, gap encontrado em implementação
A Sprint 2 persistia `CardReview` mas nunca expunha leitura via API — descoberto ao implementar a Home (último deck estudado, gráfico de estatísticas precisam de histórico de revisão, que não existia de nenhuma outra forma). Adicionado `GET /api/v1/reviews/` (`CardReviewListView`, Generic `ListAPIView`) + `CardReviewRepository.find_by_owner()` — mesmo padrão de todo endpoint já existente (owner_id obrigatório, Generic View sobre repositório Motor). Corrige a claim original deste documento ("nenhum impacto no backend") — o impacto é real, mas mínimo e contido (um método de repositório + uma view + uma rota, reaproveitando tudo que a Sprint 2 já construiu).

### D7 — Meta de estudo: armazenada no cliente (`localStorage`), não no backend
"Meta de estudo" (tarefa 3.2) não tem nenhum modelo/campo no backend — diferente do histórico de revisões (D6), que era um dado histórico já existente só sem endpoint, uma "meta" é uma preferência que nunca foi definida em nenhum spec (quantos cards? por dia? por semana?). Inventar um schema de backend agora, sem esse requisito de produto claro, seria design especulativo. A meta fica em `localStorage` (número de cards/dia, com um default), e "% alcançado" é calculado client-side comparando contra `GET /api/v1/reviews/` do dia. Documentado explicitamente aqui — não escondido — porque é uma limitação real: a meta não persiste entre dispositivos/navegadores até uma sprint futura decidir o modelo de dados correto para isso.

### D8 — `CardReview.deck_id` denormalizado, para evitar uma cadeia de requests que estoura o throttle
Testado num navegador real, "último deck estudado" precisava de `GET /reviews/` → `GET /cards/{id}/` → `GET /decks/{id}/`. Combinado com o double-effect do React 18 StrictMode em dev (que dobra a chamada de `/reviews/`), a cadeia completa (até 4 requests) estourava o throttle de 3 req/s (Sprint 1), retornando 429. `CardReview` ganhou `deck_id`, denormalizado a partir de `Card.deck_id` no momento da revisão (disponível de graça em `CardReviewView.post()`) — a SPA passa a buscar o deck em 1 request, não 2.
- **Por que é seguro denormalizar isso**: `deck_id` é uma referência estável — nunca muda depois que o card é criado. Diferente de denormalizar um título/nome de deck (que mudaria se o usuário renomeasse o deck depois, deixando revisões antigas com um nome desatualizado), uma referência (ID) nunca fica "stale" no mesmo sentido — só deixaria de resolver se o deck fosse deletado, um caso já tratado (a Home lida com a busca do deck falhando).
- **Alternativa considerada**: aumentar o throttle. Rejeitada — 3 req/s é uma decisão de segurança da Sprint 1, não deve ser afrouxada só pra acomodar uma cadeia de requests do frontend que dá pra evitar.

### D9 — Login por e-mail/senha além do Google OAuth, seed com senha conhecida
Ao testar a tela de login (D anterior: Google OAuth), surgiu a pergunta "só dá pra logar com Google?" — não, Django/allauth já suportam e-mail/senha nativamente, só não estava exposto. Adicionado `dj_rest_auth.views.LoginView` em `/auth/login/` e um segundo formulário em `LoginPage.jsx`, sem exigir nenhuma credencial externa (ao contrário do Google, que depende de `GOOGLE_OAUTH_CLIENT_ID`/`SECRET` reais). Dois bugs de configuração do allauth foram encontrados e corrigidos no processo (`ACCOUNT_LOGIN_METHODS` ausente — allauth 65.x default é login por `username`, incompatível com `USERNAME_FIELD = "email"`; `ACCOUNT_SIGNUP_FIELDS` no formato errado — dict em vez de lista de strings com `"*"`, ambos confirmados por inspeção direta do código do allauth). `seed_decks.py` também foi corrigido para setar a senha (`anki12345`) incondicionalmente em todo usuário seedado a cada run — a condição original deixava usuários pré-existentes com senha "usável" mas vazia (`is_password_usable("")` do Django retorna `True`).
- **Fora de escopo, deliberadamente**: cadastro de conta nova (tela de registro) e vínculo de conta quando Google e senha compartilham o mesmo e-mail — levantamento de requisitos feito, decisão de produto pendente (ver PRD.md 7.1). Login por e-mail/senha aqui só serve usuários já existentes (seed).

## Risks / Trade-offs

- **[Resolvido nesta sprint]** Login de UI real (Google + e-mail/senha) foi implementado — o risco original ("sem tela de login, JWT só manual") não se aplica mais; o fluxo manual documentado no `frontend/README.md` virou alternativa opcional, não o caminho principal.
- **[Risco]** Tokens extraídos "à mão" de um CSS de 4229 linhas podem divergir sutilmente do visual original do template. → **Mitigação**: tarefa 3.6 (auditoria de consistência visual) existe exatamente para isso — checklist comparando cada tela contra os tokens documentados, não confiança cega na extração inicial.
- **[Trade-off]** `fetch` nativo sem camada de cache (D3) significa que a Home pode refazer requisições desnecessárias em re-renders — aceitável no volume de Sprint 3 (poucas chamadas, uso pessoal/portfólio), reavaliado se o padrão de telas crescer.

## Migration Plan

1. Scaffold Vite + React + `react-router` em `frontend/`.
2. Auditar `refs/Ashley_files/style.css` e produzir o arquivo de tokens (cor, tipografia, espaçamento).
3. Componentes base (layout com sidebar, card, botão) usando os tokens.
4. Camada fina de API client (`fetch` + hooks) apontando para `/api/v1/...`.
5. Tela Home: card de último deck estudado, meta de estudo, gráfico de estatísticas (Chart.js).
6. Exportação do gráfico para PDF (`jsPDF`).
7. Menu lateral com as 4 seções (decks/categorias/relatórios/chat IA placeholder).
8. Auditoria de consistência visual (checklist manual contra os tokens).
- **Rollback**: sem dados/infra envolvidos — rollback é `git revert`/descartar a branch.

## Open Questions

- Nenhuma decisão de arquitetura pendente — as três decisões com trade-off real (D1–D3) já foram confirmadas com o usuário antes deste documento.
