## Why

Auditoria pré-Sprint 6 via `backend-mentor` (verificada por grep/leitura de código, não suposição) encontrou que o backend tem CRUD completo de Deck/Card/Category desde a Sprint 2 — e agora, com a Sprint 6, ganha soft delete, edição completa e meta de estudo — mas o frontend nunca ganhou uma tela pra usar nada disso. `App.jsx` tem `/decks` como `<PlaceholderPage>` desde a Sprint 3; nenhum arquivo em `frontend/src` faz `POST`/`PATCH`/`DELETE` pra API; até `setDailyGoal()` (`lib/goal.js`, a meta client-side da Sprint 3) existe mas nunca é chamada em componente nenhum. Hoje o produto só é populável via `seed_decks`/curl — sem esta sprint, a Sprint 6 entregaria capacidade de backend que nenhum usuário final consegue acionar.

## What Changes

- Tela `/decks` real, substituindo o `PlaceholderPage` — lista os decks do usuário.
- Criar/editar/excluir deck (título, descrição, categoria, `daily_review_goal`), com confirmação de exclusão avisando a janela de retenção de 7 dias (soft delete da Sprint 6).
- Dentro de um deck: listar/criar/editar/excluir cards (word/translation/example/tags), mesma confirmação de exclusão.
- Gerenciamento mínimo de categoria (listar + criar) — necessário pra alimentar o seletor de categoria do formulário de deck, que hoje não tem nenhuma fonte de dado real.

## Capabilities

### New Capabilities
- `deck-management-ui`: tela de listagem, criação, edição e exclusão de Deck.
- `card-management-ui`: listagem, criação, edição e exclusão de Card dentro de um Deck.
- `category-management-ui`: listagem e criação mínima de Category, consumida pelo formulário de Deck.

### Modified Capabilities
(nenhuma — não há capability canônica de frontend de decks/cards arquivada em `openspec/specs/`; os itens acima entram como capabilities novas)

## Impact

- Frontend: nova rota/página substituindo `PlaceholderPage` em `/decks`; formulários de criação/edição de Deck e Card; modais/confirmações de exclusão; um cliente mínimo de categoria (listar + criar). Reaproveita os tokens de design já auditados (Sprint 3/4) e o tratamento de `403` da Sprint 6.
- Sem mudança de contrato de API — consome os endpoints já existentes (`POST`/`PATCH`/`DELETE` de `/decks/`, `/cards/`, `/categories/`), todos já implementados desde a Sprint 2/6.
- Fora de escopo, registrado como gap separado (`PRD.md` §7.1): a tela de estudo em si (revisar um card, avaliar again/hard/good/easy) — não existe em nenhuma sprint do roadmap, é o gap mais fundamental do produto, precisa de levantamento de requisitos próprio via `backend-mentor` antes de virar sprint.
