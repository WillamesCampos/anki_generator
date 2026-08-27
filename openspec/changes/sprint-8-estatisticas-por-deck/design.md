## Context

A Home (Sprint 3) calcula tudo no cliente a partir de `GET /api/v1/reviews/`: `computeRatingDistribution` (todos os decks misturados, alimenta o gráfico) e `computeGoalProgress` (filtra por `toDateString()` no fuso do navegador, alimenta "cards hoje"). Isso funciona hoje porque o volume de `CardReview` por usuário ainda é pequeno (seed), mas não escala — trazer todo o histórico pra API só pra somar em JavaScript cresce linearmente com o uso real do produto.

`CardReview` já tem tudo que esta sprint precisa, sem mudança de schema: `owner_id`, `deck_id` (denormalizado desde a Sprint 3, ver `deck_id` em `card_review.py`), `rating`, `reviewed_at`. O índice atual da collection `card_reviews` (`CARD_REVIEWS_INDEXES` em `schemas.py`) cobre `owner_id`, `card_id`, `reviewed_at` e o composto `(owner_id, card_id)` — **não cobre `deck_id`**, então o novo padrão de query desta sprint (filtrar por `deck_id`+`owner_id`, com corte por data) precisa de um índice novo.

**Dependência**: esta sprint (renumerada algumas vezes conforme mais sprints foram inseridas via `backend-mentor` — hoje é a Sprint 8, depois de a Sprint 7 de gerenciamento de Deck/Card no frontend ter sido inserida) agora depende de dois campos que só existem a partir da Sprint 6 — `Deck.deleted_at` (soft delete) e `Deck.daily_review_goal` (meta por deck, substituindo a antiga meta global client-side da Sprint 3). Não implementar antes da Sprint 6 estar concluída.

## Goals / Non-Goals

**Goals:**
- Endpoint dedicado, escopado por deck e por tenant, que devolve o que o gráfico da Home precisa: distribuição por rating, revisados hoje, e progresso contra `daily_review_goal` (Sprint 6).
- Cálculo via agregação MongoDB, não Python — inclusive a exclusão de registros soft-deletados (`deleted_at`, Sprint 6).
- Dropdown na Home selecionando qualquer deck do usuário, com o deck mais recente como default.

**Non-Goals:**
- Dashboard de analytics completo (tendência ao longo do tempo, comparação entre decks, streaks) — fora de escopo, pode virar sprint futura se houver demanda real.
- Criar o campo `daily_review_goal` em si, ou o mecanismo de soft delete — ambos são entregues pela Sprint 6; esta sprint só consome os dois.

## Decisions

### D1 — Agregação única via `$facet`, não duas queries separadas
A resposta do endpoint precisa de duas coisas (distribuição por rating + contagem de hoje) que, calculadas ingenuamente, seriam duas queries Mongo separadas. Usar `$facet` numa única chamada de agregação (`$match` comum por `owner_id`+`deck_id`+`deleted_at: null` — exclui revisões de cards/decks soft-deletados na Sprint 6 —, depois dois sub-pipelines: um `$group` por `rating`, outro `$match` adicional por `reviewed_at >= início do dia` + `$count`) — um round-trip só ao Mongo, não dois. O progresso contra `daily_review_goal` (Sprint 6) é calculado depois, em Python, dividindo a contagem de hoje pelo valor do campo — não precisa entrar na agregação, é só uma divisão sobre um resultado que a agregação já devolveu.

### D2 — Novo índice composto `(owner_id, deck_id, reviewed_at)` em `card_reviews`
O índice atual não cobre consultas por `deck_id`. Adicionado `([("owner_id", 1), ("deck_id", 1), ("reviewed_at", 1)], {})` em `CARD_REVIEWS_INDEXES` (`schemas.py`) — fonte única já usada por `MongoDBConnectionManager.create_indexes()`, criado automaticamente na inicialização (mesmo mecanismo da Sprint 2, sem migração manual separada).

### D3 — Isolamento multi-tenant: verificar posse do deck antes de agregar
Mesmo padrão já usado em `CardReviewView`/`DeckDetailView`: o endpoint recebe `deck_id` na URL, mas a query real filtra por `owner_id` (do JWT) **e** `deck_id` — nunca confia no `deck_id` da URL isoladamente. Se o deck não existe ou não pertence ao usuário, `404` (não vazar existência de decks de outros tenants).

### D4 — Frontend: dropdown com deck mais recente como default
Sem seleção manual, a Home continua mostrando o deck mais recentemente estudado — o dado já vem de `GET /api/v1/reviews/` (mais recente primeiro) como hoje. O `deck_id` resolvido (automático ou selecionado manualmente) dispara `GET /api/v1/decks/{deck_id}/statistics/`, que alimenta tanto o card superior (nome/descrição) quanto o gráfico. Selecionar manualmente no dropdown troca o título do card de "Último deck estudado" para "Deck estudado" (ver `dropdown-deck-home` em `PROMPT_REFINADO.md`).

### D5 — Separação visual: padding + borda, sem componente novo
Ajuste puramente CSS no layout já existente da Home (`HomePage.jsx`/tokens) — espaço entre o grid superior (último deck + meta) e o card de Estatísticas, borda mais grossa nos `ui-card`. Não introduz componente novo, só tokens de espaçamento/borda já existentes ou levemente ajustados.

## Risks / Trade-offs

- **[Risco]** "Revisado hoje" no card de Estatísticas (novo, calculado no servidor em UTC) pode divergir por algumas horas do "cards hoje" do card de Meta de estudo (ainda client-side, usa `toDateString()` no fuso do navegador) — um usuário em fuso muito distante de UTC pode ver os dois números discordarem perto da virada do dia. → **Mitigação**: aceitável para esta sprint (ambos os cards já eram calculados de formas diferentes antes); documentar aqui a inconsistência para revisitar se virar uma reclamação real de usuário — não vale unificar timezone agora sem um caso de uso concreto.
- **[Risco]** Índice novo em `card_reviews` significa mais um índice pra manter conforme a collection cresce. → **Mitigação**: composto e alinhado ao padrão de query real (owner+deck+data), não um índice especulativo; mesmo trade-off já aceito nos índices existentes das Sprints 0-2.

## Migration Plan

Sem migração de dados — só um índice novo (criado automaticamente pelo `MongoDBConnectionManager.create_indexes()` já existente) e um endpoint novo. Nenhum dado histórico precisa de backfill: `deck_id`/`reviewed_at` já existem em todo `CardReview` desde a Sprint 3.
