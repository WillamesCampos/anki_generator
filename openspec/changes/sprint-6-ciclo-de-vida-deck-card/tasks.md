## 1. Soft delete — schema e filtro

- [ ] 1.1 `deleted_at: Optional[datetime]` em `Deck` e `Card` (`apps/decks/domain/entities/`) — `to_dict()`/`from_dict()` atualizados
- [ ] 1.2 Helper único de filtro base (`owner_id` + `deleted_at: None`) usado por todo método de leitura em `DeckRepository`, `CardRepository`, `CategoryRepository` — ver D1 em design.md
- [ ] 1.3 Auditar e atualizar toda query existente (`find_by_owner`, `find_by_deck_id`, busca de cards devidos do FSRS) pra usar o helper, não filtro manual

## 2. Exclusão e cascade

- [ ] 2.1 `DELETE /api/v1/decks/{deck_id}/` — soft delete do deck + cascade pra todos os cards do deck (ver D2 em design.md)
- [ ] 2.2 `DELETE /api/v1/cards/{card_id}/` — soft delete individual
- [ ] 2.3 Confirmar que `CardReview` nunca é tocada por nenhuma dessas operações (ver D3 em design.md)

## 3. Purge automático

- [ ] 3.1 `apps/decks/tasks.py` (novo) — task Celery `purge_soft_deleted` que remove fisicamente `Deck`/`Card` com `deleted_at` há mais de 7 dias
- [ ] 3.2 Registrar a task em `CELERY_BEAT_SCHEDULE` (`core/settings/base.py`), rodando diariamente

## 4. Meta por deck e edição completa

- [ ] 4.1 `daily_review_goal: Optional[int]` em `Deck` — `to_dict()`/`from_dict()` atualizados
- [ ] 4.2 `PATCH /api/v1/decks/{deck_id}/` aceita `title`, `category_id`, `daily_review_goal` — `owner_id`/`created_by`/`updated_by` nunca aceitos do payload
- [ ] 4.3 `PATCH /api/v1/cards/{card_id}/` aceita conteúdo (word/translation/example) e `tags`

## 5. Frontend — tratamento de 403

- [ ] 5.1 `apiFetch` (`frontend/src/api/client.js`) trata `403` distintamente de outros erros — a partir da Sprint 5 (permissão por grupo) esse status passa a ser possível de verdade, algo que não existia até aqui
- [ ] 5.2 Mensagem de UI clara ("você não tem permissão para isso") em vez do erro genérico atual

## 6. Testes automatizados

- [ ] 6.1 Soft delete: `deleted_at` setado corretamente, registro some das leituras normais
- [ ] 6.2 Cascade: apagar um deck soft-deleta todos os seus cards
- [ ] 6.3 `CardReview` sobrevive à exclusão do card/deck associado
- [ ] 6.4 Purge: registros com mais de 7 dias são removidos fisicamente, registros mais recentes são preservados
- [ ] 6.5 `daily_review_goal` editável via PATCH, ausente por padrão em deck novo
- [ ] 6.6 PATCH de deck/card ignora `owner_id`/`created_by`/`updated_by` enviados no payload

## 7. Documentação

- [ ] 7.1 Atualizar `PRD.md` (Sprint 6) marcando as tarefas concluídas
- [ ] 7.2 Atualizar `CHANGELOG.md` com a entrada `[Sprint 6]`
- [ ] 7.3 Marcar o item "Cascade delete de CardReview" em `PRD.md` §7.1 como resolvido (já feito na formalização, conferir que ficou consistente)
