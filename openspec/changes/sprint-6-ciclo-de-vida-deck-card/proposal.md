## Why

O produto hoje só tem create/read completo de Deck/Card — falta edição real (nome, categoria, tags, meta de estudo) e uma política de exclusão. Levantamento de requisitos via `backend-mentor` definiu o que um usuário final precisa poder fazer: criar/editar/excluir deck, criar/editar/excluir card, com exclusão soft por 7 dias (não delete físico direto) e uma meta de cards a revisar por deck. Depende da Sprint 5 (audit fields/permissões) já estar pronta.

## What Changes

- `deleted_at: Optional[datetime]` em `Deck` e `Card` — soft delete por timestamp, não delete físico direto.
- Toda query de repositório existente passa a excluir registros com `deleted_at` preenchido por padrão.
- `DELETE /api/v1/decks/{deck_id}/` cascateia: marca `deleted_at` em todos os cards do deck junto — sem caso de "desvincular" (relação Card↔Deck continua 1:1, decisão explícita de não introduzir N:N agora).
- `DELETE /api/v1/cards/{card_id}/` — soft delete individual.
- Task Celery Beat diária que purga permanentemente (delete físico) registros com `deleted_at` há mais de 7 dias.
- `daily_review_goal: Optional[int]` em `Deck`, editável via `PATCH` — meta de cards a revisar daquele deck, substituindo a meta de estudo client-side global da Sprint 3.
- Edição completa de `Deck` (nome, categoria, `daily_review_goal`) e `Card` (conteúdo, tags) via `PATCH`.
- `apiFetch` (frontend) passa a tratar `403` distintamente de outros erros — a partir da Sprint 5 (permissão por grupo) esse status passa a ser possível de verdade.

## Capabilities

### New Capabilities
- `soft-delete-lifecycle`: `deleted_at` em Deck/Card, cascade Deck→Card na exclusão, filtro automático em toda leitura, purge automático após 7 dias.
- `deck-daily-review-goal`: campo `daily_review_goal` persistido e editável no Deck.
- `deck-card-full-edit`: edição completa (PATCH) de Deck e Card além do que já existe desde a Sprint 2.
- `forbidden-error-handling`: tratamento de `403` na SPA, distinto do erro genérico atual.

### Modified Capabilities
(nenhuma — `deck-card-crud-api`, da Sprint 2, nunca foi arquivada em `openspec/specs/`, então não há capability canônica pra alterar via delta; os itens acima entram como capabilities novas mesmo estendendo comportamento já existente)

## Impact

- Backend: todos os repositórios em `apps/decks/infrastructure/repositories/` ganham um filtro `deleted_at: None` centralizado; `apps/decks/views.py` ganha `DELETE` em `DeckDetailView`/`CardDetailView` com a lógica de cascade; primeira task Celery real do projeto (`apps/decks/tasks.py`, novo arquivo), agendada via Celery Beat.
- `CardReview` nunca é apagada — passa a ser excluída das estatísticas (Sprint 7) via os campos `deleted_at` de `Card`/`Deck`, resolvendo o gap de cascade delete pendente desde a Sprint 3 (`PRD.md` §7.1).
- Frontend: formulários de edição de Deck/Card, confirmação de exclusão (com aviso da janela de 7 dias), campo de meta no formulário de deck. Fora de escopo desta sprint: tela de "itens excluídos"/restauração manual — se vier a existir, é decisão de produto separada.
