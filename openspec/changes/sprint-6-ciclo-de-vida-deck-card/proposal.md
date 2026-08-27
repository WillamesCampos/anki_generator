## Why

O produto hoje só tem create/read completo de Deck/Card — falta edição real (nome, categoria, tags, meta de estudo) e uma política de exclusão. Levantamento de requisitos via `backend-mentor` definiu o que um usuário final precisa poder fazer: criar/editar/excluir deck, criar/editar/excluir card, com exclusão soft por 7 dias (não delete físico direto) e uma meta de cards a revisar por deck. Depende da Sprint 5 (audit fields/permissões) já estar pronta. Escopo ampliado numa auditoria pré-sprint via `backend-mentor`: `Category` também vira soft delete — `CategoryRepository.delete()` era delete físico sem checar se algum `Deck` ainda referenciava a categoria via `category_id`, deixando uma referência dangling.

## What Changes

- `deleted_at: Optional[datetime]` em `Deck`, `Card` e `Category` — soft delete por timestamp, não delete físico direto.
- Toda query de repositório existente passa a excluir registros com `deleted_at` preenchido por padrão.
- `DELETE /api/v1/decks/{deck_id}/` cascateia: marca `deleted_at` em todos os cards do deck junto — sem caso de "desvincular" (relação Card↔Deck continua 1:1, decisão explícita de não introduzir N:N agora).
- `DELETE /api/v1/cards/{card_id}/` — soft delete individual.
- `DELETE /api/v1/categories/{category_id}/` — soft delete; decks que referenciam a categoria são desvinculados (`category_id → None`), sem cascatear.
- Task Celery Beat diária que purga permanentemente (delete físico) registros com `deleted_at` há mais de 7 dias, nas três entidades.
- `daily_review_goal: Optional[int]` em `Deck`, editável via `PATCH` — meta de cards a revisar daquele deck, substituindo a meta de estudo client-side global da Sprint 3.
- Edição completa de `Deck` (nome, categoria, `daily_review_goal`) e `Card` (conteúdo, tags) via `PATCH`.
- `apiFetch` (frontend) passa a tratar `403` distintamente de outros erros — a partir da Sprint 5 (permissão por grupo) esse status passa a ser possível de verdade.
- **Decisão explícita de não fazer**: `find_by_user_id`/`count_by_user_id` do `DeckRepository`, código morto achado na mesma auditoria, são removidos em vez de mantidos — sem call-site em nenhuma view/teste/seed.

## Capabilities

### New Capabilities
- `soft-delete-lifecycle`: `deleted_at` em Deck/Card/Category, cascade Deck→Card na exclusão, desvínculo (não cascade) Category→Deck, filtro automático em toda leitura, purge automático após 7 dias.
- `deck-daily-review-goal`: campo `daily_review_goal` persistido e editável no Deck.
- `deck-card-full-edit`: edição completa (PATCH) de Deck e Card além do que já existe desde a Sprint 2.
- `forbidden-error-handling`: tratamento de `403` na SPA, distinto do erro genérico atual.

### Modified Capabilities
(nenhuma — `deck-card-crud-api`, da Sprint 2, nunca foi arquivada em `openspec/specs/`, então não há capability canônica pra alterar via delta; os itens acima entram como capabilities novas mesmo estendendo comportamento já existente)

## Impact

- Backend: todos os repositórios em `apps/decks/infrastructure/repositories/` ganham um filtro `deleted_at: None` centralizado; `apps/decks/views.py` ganha `DELETE` em `DeckDetailView`/`CardDetailView`/`CategoryDetailView` com a lógica de cascade/desvínculo; primeira task Celery real do projeto (`apps/decks/tasks.py`, novo arquivo), agendada via Celery Beat.
- `CardReview` nunca é apagada — passa a ser excluída das estatísticas (Sprint 8) via os campos `deleted_at` de `Card`/`Deck`, resolvendo o gap de cascade delete pendente desde a Sprint 3 (`PRD.md` §7.1).
- Frontend: só o tratamento de `403` (`forbidden-error-handling`) — os formulários de edição/exclusão de Deck/Card/Category (originalmente previstos aqui) viraram a Sprint 7 dedicada (`gerenciamento-deck-card-frontend`), achada na mesma auditoria pré-sprint: nenhuma sprint do roadmap jamais construiu uma tela real pra usar esse CRUD, `/decks` continua `PlaceholderPage` desde a Sprint 3. Fora de escopo desta e da Sprint 7: tela de "itens excluídos"/restauração manual — se vier a existir, é decisão de produto separada.
