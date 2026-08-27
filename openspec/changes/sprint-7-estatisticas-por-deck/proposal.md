## Why

A Home da Sprint 3 mistura todos os decks do usuário num único gráfico de estatísticas, sem forma de ver o desempenho de um deck específico — e "cards revisados hoje" é calculado inteiro no cliente, filtrando `GET /api/v1/reviews/` em JavaScript, o que não escala conforme o histórico de revisões cresce. Gap encontrado testando a Home de verdade, não em revisão de código; decisões de escopo já fechadas em `PROMPT_REFINADO.md` (`estatisticas-por-deck-endpoint`, `dropdown-deck-home`, `cards-revisados-hoje-sem-campo-novo`).

## What Changes

- Novo endpoint `GET /api/v1/decks/{deck_id}/statistics/`: distribuição de revisões por rating (again/hard/good/easy) + quantidade revisada hoje, escopados a `deck_id`+`owner_id`, calculados via agregação MongoDB (`$match`/`$group`) — não trazendo os documentos crus pra API.
- Dropdown na Home, acima do gráfico de Estatísticas, para selecionar qualquer deck do usuário — o gráfico passa a refletir o deck selecionado via o endpoint novo.
- Comportamento default (sem seleção manual): mostra o deck mais recentemente estudado, reaproveitando o mesmo dado hoje usado em "Último deck estudado".
- Título do card muda de "Último deck estudado" para "Deck estudado" quando o usuário seleciona manualmente um deck no dropdown.
- Separação visual entre o grid superior (último deck estudado + meta de estudo) e o card de Estatísticas — padding entre as bordas, bordas mais grossas.
- Confirmado (não muda nada): "cards revisados hoje" não precisa de campo novo persistido no `Deck` — já é derivável de `CardReview.reviewed_at`+`deck_id`, sem necessidade de job de reset diário.

## Capabilities

### New Capabilities
- `deck-statistics-api`: endpoint `GET /api/v1/decks/{deck_id}/statistics/`, agregação MongoDB de distribuição por rating + revisados hoje, escopado por deck e por tenant.
- `home-deck-selector`: dropdown de seleção de deck na Home, consumindo `deck-statistics-api`, com deck mais recente como default e troca de título do card conforme o modo (automático vs. selecionado manualmente).

### Modified Capabilities
(nenhuma — `sprint-3-frontend-base-home-dashboard` nunca foi arquivada em `openspec/specs/`, então não há capability canônica de `home-dashboard` pra alterar via delta; o comportamento da Home muda, mas via as capabilities novas acima)

## Impact

- Backend: novo endpoint em `apps/decks/urls.py` + `apps/decks/views.py`, novo método de agregação em `CardReviewRepository` (Motor/pymongo), reaproveitando o padrão de `owner_id` obrigatório já estabelecido na Sprint 2.
- Frontend: `HomePage.jsx` ganha um componente de dropdown, novo hook de dados (`useDeckStatistics` ou equivalente) e um ajuste de CSS no layout dos cards (padding + borda).
- Nenhuma mudança de schema no `Deck`/`CardReview` — a persistência necessária já existe desde a Sprint 3 (`CardReview.deck_id`/`reviewed_at`).
