## Context

A Home (Sprint 3) calcula tudo no cliente a partir de `GET /api/v1/reviews/`: `computeRatingDistribution` (todos os decks misturados, alimenta o gráfico) e `computeGoalProgress` (filtra por `toDateString()` no fuso do navegador, alimenta "cards hoje"). Isso funciona hoje porque o volume de `CardReview` por usuário ainda é pequeno (seed), mas não escala — trazer todo o histórico pra API só pra somar em JavaScript cresce linearmente com o uso real do produto.

`CardReview` já tem tudo que esta sprint precisa, sem mudança de schema: `owner_id`, `deck_id` (denormalizado desde a Sprint 3, ver `deck_id` em `card_review.py`), `rating`, `reviewed_at`. O índice atual da collection `card_reviews` (`CARD_REVIEWS_INDEXES` em `schemas.py`) cobre `owner_id`, `card_id`, `reviewed_at` e o composto `(owner_id, card_id)` — **não cobre `deck_id`**, então o novo padrão de query desta sprint (filtrar por `deck_id`+`owner_id`, com corte por data) precisa de um índice novo.

**Dependência**: esta sprint (renumerada mais de uma vez conforme sprints novas foram inseridas via `backend-mentor` — hoje é a Sprint 10, depois de a Sprint 7 de gerenciamento de Deck/Card, a Sprint 8 de pipeline de testes/CI e a Sprint 9 de tela de estudo terem sido inseridas) agora depende de dois campos que só existem a partir da Sprint 6 — `Deck.deleted_at` (soft delete) e `Deck.daily_review_goal` (meta por deck, substituindo a antiga meta global client-side da Sprint 3). Não implementar antes da Sprint 6 estar concluída.

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

### D6 — Revisão (pós-Sprint 9): dropdown (D4) descartado
**Histórico**: D4 (acima) foi decidido antes da Sprint 9 existir, quando a única forma de ver estatísticas de um deck específico fora do "mais recente" seria um dropdown novo na Home.

**Motivo da reversão**: a Sprint 9 introduziu o componente `RatingDistributionChart`, compartilhado entre a Home e `DeckDetailPage` (Sprint 7). Isso significa que hoje, sem nenhum código novo, já existe um caminho para ver o gráfico de qualquer deck do usuário: Home → `/decks` → abrir o deck → ver as estatísticas dele ali, com o mesmo componente visual. O dropdown proposto em D4 resolveria o mesmo problema por um caminho a mais (sem sair da Home) — mas é o mesmo tipo de "navegação duplicada para o mesmo destino" já identificado e rejeitado na Sprint 9 para o item "Estudar" do menu lateral (ver Sprint 9, tarefa 9.9, e `design.md` daquela sprint).

**Trade-off reconhecido, não escondido**: descartar o dropdown custa uma conveniência real, ainda que pequena — ver estatísticas de outro deck sem sair da Home. Não há indício de demanda concreta por essa conveniência (nenhum uso real do produto expôs essa necessidade); se aparecer depois, revisitar como sprint própria, e não reabrir esta decisão sem um caso de uso real.

**Decisão**: 3.2/3.4/3.5 do `tasks.md` (dropdown, troca de deck, troca de título) descartados. 3.3 (default = deck mais recente) permanece como comportamento já existente, não como tarefa nova. D4 permanece registrada acima como histórico da decisão original, agora superada por esta.

## Risks / Trade-offs

- **[Risco]** "Revisado hoje" no card de Estatísticas (novo, calculado no servidor em UTC) pode divergir por algumas horas do "cards hoje" do card de Meta de estudo (ainda client-side, usa `toDateString()` no fuso do navegador) — um usuário em fuso muito distante de UTC pode ver os dois números discordarem perto da virada do dia. → **Mitigação**: aceitável para esta sprint (ambos os cards já eram calculados de formas diferentes antes); documentar aqui a inconsistência para revisitar se virar uma reclamação real de usuário — não vale unificar timezone agora sem um caso de uso concreto.
- **[Risco]** Índice novo em `card_reviews` significa mais um índice pra manter conforme a collection cresce. → **Mitigação**: composto e alinhado ao padrão de query real (owner+deck+data), não um índice especulativo; mesmo trade-off já aceito nos índices existentes das Sprints 0-2.

## Migration Plan

Sem migração de dados — só um índice novo (criado automaticamente pelo `MongoDBConnectionManager.create_indexes()` já existente) e um endpoint novo. Nenhum dado histórico precisa de backfill: `deck_id`/`reviewed_at` já existem em todo `CardReview` desde a Sprint 3.
