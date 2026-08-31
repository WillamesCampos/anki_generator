## Why

Auditoria pré-Sprint 6 via `backend-mentor` (verificada por grep/leitura de código, não suposição) encontrou que o backend tem CRUD completo de Deck/Card/Category desde a Sprint 2 — e agora, com a Sprint 6, ganha soft delete, edição completa e meta de estudo — mas o frontend nunca ganhou uma tela pra usar nada disso. `App.jsx` tem `/decks` como `<PlaceholderPage>` desde a Sprint 3; nenhum arquivo em `frontend/src` faz `POST`/`PATCH`/`DELETE` pra API; até `setDailyGoal()` (`lib/goal.js`, a meta client-side da Sprint 3) existe mas nunca é chamada em componente nenhum. Hoje o produto só é populável via `seed_decks`/curl — sem esta sprint, a Sprint 6 entregaria capacidade de backend que nenhum usuário final consegue acionar.

## What Changes

- Tela `/decks` real, substituindo o `PlaceholderPage` — lista os decks do usuário.
- Criar/editar/excluir deck (título, descrição, categoria, `daily_review_goal`), com confirmação de exclusão avisando a janela de retenção de 7 dias (soft delete da Sprint 6).
- O detalhe de um deck exibe somente a quantidade de cards e o botão "Ver todos os cards"; não baixa a coleção completa.
- Página dedicada `/decks/:deckId/cards` com o formulário de criação antes da lista e paginação de 10 cards por página para listar/criar/editar/excluir cards (`front`/`back`/`front_description`/`back_description`/tags), mantendo os rótulos visíveis em português e a mesma confirmação de exclusão.
- O detalhe do deck exibe a distribuição histórica das revisões daquele deck nas quatro classificações Anki/FSRS (`again`, `hard`, `good`, `easy`), reutilizando o gráfico e os rótulos já adotados na Home.
- Novo endpoint `GET /api/v1/cards/count/?deck_id=...`, que executa apenas a contagem escopada pelo dono e retorna somente `{ "count": N }`.
- Renomeação do contrato e da persistência de Card em todo o monorepo: `word` → `front`, `translation` → `back`, `example_original` → `front_description`, `example_translated` → `back_description`. A versão intermediária em português também é migrada para o contrato final em inglês.
- Rate limit global alterado de 3 para 10 requisições por segundo por decisão explícita do usuário.
- Leituras Motor disparadas pelas views DRF síncronas passam por um event loop persistente, eliminando o `500` intermitente observado quando detalhe e cards eram consultados em paralelo.
- Gerenciamento mínimo de categoria (listar + criar) — necessário pra alimentar o seletor de categoria do formulário de deck, que hoje não tem nenhuma fonte de dado real.

## Capabilities

### New Capabilities
- `deck-management-ui`: tela de listagem, criação, edição e exclusão de Deck.
- `card-management-ui`: listagem, criação, edição e exclusão de Card dentro de um Deck.
- `category-management-ui`: listagem e criação mínima de Category, consumida pelo formulário de Deck.
- `card-count-api`: contagem mínima de cards por deck, sem materializar a lista.
- `api-read-resilience`: orçamento de 10 req/s e acesso Motor seguro sob requisições concorrentes.
- `card-list-pagination-api`: listagem de cards por deck paginada em 10 itens.
- `deck-detail-statistics-ui`: gráfico histórico das classificações do deck no detalhe.

### Modified Capabilities
(nenhuma — não há capability canônica de frontend de decks/cards arquivada em `openspec/specs/`; os itens acima entram como capabilities novas)

## Impact

- Frontend: novas rotas/páginas em `/decks`, `/decks/novo`, `/decks/:deckId` e `/decks/:deckId/cards`; formulários de criação/edição de Deck e Card; modais/confirmações de exclusão; um cliente mínimo de categoria. Reaproveita os tokens de design já auditados (Sprint 3/4) e o tratamento de `403` da Sprint 6.
- Backend: novo endpoint mínimo de contagem, contrato de Card renomeado, migração dos documentos Mongo existentes, throttle de 10 req/s, paginação dedicada de cards, uma ponte assíncrona persistente entre DRF síncrono e Motor e antecipação do endpoint agregado por deck já especificado em `sprint-9-estatisticas-por-deck`.
- Fora de escopo, registrado como gap separado (`PRD.md` §7.1): a tela de estudo em si (revisar um card, avaliar again/hard/good/easy) — não existe em nenhuma sprint do roadmap, é o gap mais fundamental do produto, precisa de levantamento de requisitos próprio via `backend-mentor` antes de virar sprint.
