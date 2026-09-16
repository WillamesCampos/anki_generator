## 1. Backend — índice e agregação

- [x] 1.1 Adicionar índice composto `(owner_id, deck_id, reviewed_at)` em `CARD_REVIEWS_INDEXES` (`schemas.py`) — ver D2 em design.md
- [x] 1.2 Novo método `CardReviewRepository.get_deck_statistics(owner_id, deck_id)` — agregação `$facet` (distribuição por rating + contagem de hoje) num único round-trip ao Mongo, ver D1 em design.md
- [x] 1.3 Verificar posse do deck (`owner_id`+`deck_id`) antes de agregar — `404` se o deck não existe ou não pertence ao usuário, nunca vazar existência (ver D3 em design.md)
- [x] 1.4 Agregação exclui `CardReview` cujo `card_id`/`deck_id` associado está soft-deletado (`deleted_at` preenchido, ver Sprint 6)
- [x] 1.5 Resposta inclui progresso contra `daily_review_goal` do deck (revisado hoje / meta)

## 2. Backend — endpoint

- [x] 2.1 `GET /api/v1/decks/{deck_id}/statistics/` — nova view em `apps/decks/views.py`, reaproveitando o padrão de autenticação/permissão já usado em `CardReviewView`
- [x] 2.2 Rota registrada em `apps/decks/urls.py`
- [x] 2.3 Testes automatizados (pytest): distribuição correta por rating, contagem de hoje correta, isolamento multi-tenant (deck de outro usuário → 404), deck sem reviews → resposta zerada sem erro

## 3. Frontend — endpoint client + dropdown

- [x] 3.1 `fetchDeckStatistics(deckId)` em `frontend/src/api/decks.js`, consumindo o endpoint novo
- [x] ~~3.2 Dropdown de seleção de deck na Home, acima do gráfico de Estatísticas, populado via `GET /api/v1/decks/`~~
  **Descartado** (revisão pós-Sprint 9, ver D6 em design.md): `DeckDetailPage` + `RatingDistributionChart` compartilhado já cobrem o caso de uso por outro caminho de navegação, sem duplicar o já existente (mesmo padrão rejeitado pro item "Estudar" do menu lateral na Sprint 9).
- [x] ~~3.3 Sem seleção manual, resolve o deck mais recentemente estudado como default~~
  **Descartado como tarefa isolada** — o comportamento em si já existe (não depende do dropdown): a Home mostra o deck mais recentemente estudado desde a Sprint 3, sem nenhuma seleção manual possível.
- [x] ~~3.4 Ao selecionar um deck manualmente, dispara `fetchDeckStatistics` e atualiza o gráfico~~
  **Descartado** — dependia do dropdown (3.2).
- [x] ~~3.5 Título do card muda entre "Último deck estudado" (automático) e "Deck estudado" (seleção manual) — ver D4 em design.md~~
  **Descartado** — dependia do dropdown (3.2).

## 4. Frontend — layout

- [x] 4.1 Padding entre o grid superior (último deck estudado + meta de estudo) e o card de Estatísticas
  **Resolvido** como efeito colateral do design system global da Sprint 9 (D11 daquela sprint) — não implementado pensando nesta sprint.
- [x] 4.2 Bordas mais grossas nos `ui-card` da Home — ver D5 em design.md
  **Resolvido** pela mesma globalização de `Card.css` na Sprint 9.

## 5. Documentação

- [x] 5.1 Atualizar `PRD.md` (Sprint 10) marcando as tarefas concluídas, com notas de implementação
- [x] 5.2 Atualizar `CHANGELOG.md` com a entrada `[Sprint 10]`
- [x] ~~5.3 Validar manualmente no navegador — trocar de deck no dropdown, conferir que o gráfico muda e o título do card também~~
  **Descartado** — testava exclusivamente o fluxo do dropdown, que não será construído.
