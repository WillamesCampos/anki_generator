## 1. Backend — índice e agregação

- [ ] 1.1 Adicionar índice composto `(owner_id, deck_id, reviewed_at)` em `CARD_REVIEWS_INDEXES` (`schemas.py`) — ver D2 em design.md
- [ ] 1.2 Novo método `CardReviewRepository.get_deck_statistics(owner_id, deck_id)` — agregação `$facet` (distribuição por rating + contagem de hoje) num único round-trip ao Mongo, ver D1 em design.md
- [ ] 1.3 Verificar posse do deck (`owner_id`+`deck_id`) antes de agregar — `404` se o deck não existe ou não pertence ao usuário, nunca vazar existência (ver D3 em design.md)
- [ ] 1.4 Agregação exclui `CardReview` cujo `card_id`/`deck_id` associado está soft-deletado (`deleted_at` preenchido, ver Sprint 6) — pré-requisito: `deleted_at` já existe em `Deck`/`Card`
- [ ] 1.5 Resposta inclui progresso contra `daily_review_goal` do deck (revisado hoje / meta), campo que só existe a partir da Sprint 6

## 2. Backend — endpoint

- [ ] 2.1 `GET /api/v1/decks/{deck_id}/statistics/` — nova view em `apps/decks/views.py`, reaproveitando o padrão de autenticação/permissão já usado em `CardReviewView`
- [ ] 2.2 Rota registrada em `apps/decks/urls.py`
- [ ] 2.3 Testes automatizados (pytest): distribuição correta por rating, contagem de hoje correta, isolamento multi-tenant (deck de outro usuário → 404), deck sem reviews → resposta zerada sem erro

## 3. Frontend — endpoint client + dropdown

- [ ] 3.1 `fetchDeckStatistics(deckId)` em `frontend/src/api/decks.js` (ou arquivo equivalente), consumindo o endpoint novo
- [ ] 3.2 Dropdown de seleção de deck na Home, acima do gráfico de Estatísticas, populado via `GET /api/v1/decks/`
- [ ] 3.3 Sem seleção manual, resolve o deck mais recentemente estudado como default (reaproveitando a lógica já existente de "último deck estudado")
- [ ] 3.4 Ao selecionar um deck manualmente, dispara `fetchDeckStatistics` e atualiza o gráfico
- [ ] 3.5 Título do card muda entre "Último deck estudado" (automático) e "Deck estudado" (seleção manual) — ver D4 em design.md

## 4. Frontend — layout

- [ ] 4.1 Padding entre o grid superior (último deck estudado + meta de estudo) e o card de Estatísticas
- [ ] 4.2 Bordas mais grossas nos `ui-card` da Home — ver D5 em design.md

## 5. Documentação

- [ ] 5.1 Atualizar `PRD.md` (Sprint 10) marcando as tarefas concluídas, com notas de implementação
- [ ] 5.2 Atualizar `CHANGELOG.md` com a entrada `[Sprint 10]`
- [ ] 5.3 Validar manualmente no navegador (login já funciona desde a Sprint 3) — trocar de deck no dropdown, conferir que o gráfico muda e o título do card também
