## 1. Soft delete — schema e filtro

- [x] 1.1 `deleted_at: Optional[datetime]` em `Deck`, `Card` e `Category` (`apps/decks/domain/entities/`) — `to_dict()`/`from_dict()` atualizados
- [x] 1.2 Helper único de filtro base (`owner_id` + `deleted_at: None`) usado por todo método de leitura em `DeckRepository`, `CardRepository`, `CategoryRepository` — ver D1 em design.md (`schemas.base_filter`)
- [x] 1.3 Auditar e atualizar toda query existente (`find_by_owner`, `find_by_deck_id`, busca de cards devidos do FSRS) pra usar o helper, não filtro manual — aplicado a todo método de leitura das 3 entidades, incluindo os métodos legados do protótipo antigo (`find_by_word`/`find_similar_cards`/`find_duplicates`/`exists_by_word`, mantidos por decisão da Sprint 2 pro futuro agente de IA reaproveitar)

## 2. Exclusão e cascade

- [x] 2.1 `DELETE /api/v1/decks/{deck_id}/` — soft delete do deck + cascade pra todos os cards do deck (ver D2 em design.md) — repositório pronto (`DeckRepository.delete`), view a confirmar
- [x] 2.2 `DELETE /api/v1/cards/{card_id}/` — soft delete individual — repositório pronto (`CardRepository.delete`), view a confirmar
- [x] 2.3 `DELETE /api/v1/categories/{category_id}/` — soft delete + desvincula (`category_id = None`) todos os decks que referenciam a categoria, sem cascatear (ver D6 em design.md) — repositório pronto (`CategoryRepository.delete` + `DeckRepository.unlink_category`), view a confirmar/adicionar
- [x] 2.4 Confirmar que `CardReview` nunca é tocada por nenhuma dessas operações (ver D3 em design.md) — satisfeito por construção: nenhum código de soft delete/cascade/desvínculo toca `CardReviewRepository`/`card_reviews`

## 3. Purge automático

- [x] 3.1 `apps/decks/tasks.py` (novo) — task Celery `purge_soft_deleted` que remove fisicamente `Deck`/`Card`/`Category` com `deleted_at` há mais de 7 dias — testado rodando de verdade contra Mongo real (0 purgados, sem dados soft-deletados ainda, sem erro)
- [x] 3.2 Registrar a task em `CELERY_BEAT_SCHEDULE` (`core/settings/base.py`), rodando diariamente

## 4. Meta por deck e edição completa

- [x] 4.1 `daily_review_goal: Optional[int]` em `Deck` — `to_dict()`/`from_dict()` atualizados
- [x] 4.2 `PATCH /api/v1/decks/{deck_id}/` aceita `title`, `category_id`, `daily_review_goal` — `owner_id`/`created_by`/`updated_by` nunca aceitos do payload
- [x] 4.3 `PATCH /api/v1/cards/{card_id}/` aceita conteúdo (word/translation/example) e `tags` — já funcionava (Sprint 2), confirmado

## 5. Limpeza de código morto

- [x] 5.1 Remover `DeckRepository.find_by_user_id`/`count_by_user_id` — sem call-site em view/teste/seed (achado na auditoria pré-sprint, ver D6 em design.md)

## 6. Frontend — tratamento de 403

- [x] 6.1 `apiFetch` (`frontend/src/api/client.js`) trata `403` distintamente de outros erros — a partir da Sprint 5 (permissão por grupo) esse status passa a ser possível de verdade, algo que não existia até aqui
- [x] 6.2 Mensagem de UI clara ("você não tem permissão para isso") em vez do erro genérico atual — `HomePage.jsx` (único ponto do frontend que renderiza erro de fetch hoje)

## 7. Testes automatizados

- [x] 7.1 Soft delete: `deleted_at` setado corretamente, registro some das leituras normais (Deck/Card/Category)
- [x] 7.2 Cascade: apagar um deck soft-deleta todos os seus cards
- [x] 7.3 Desvínculo: apagar uma categoria referenciada por decks zera `category_id` nesses decks, sem apagá-los
- [x] 7.4 `CardReview` sobrevive à exclusão do card/deck associado
- [x] 7.5 Purge: registros com mais de 7 dias são removidos fisicamente, registros mais recentes são preservados
- [x] 7.6 `daily_review_goal` editável via PATCH, ausente por padrão em deck novo
- [x] 7.7 PATCH de deck/card ignora `owner_id`/`created_by`/`updated_by` enviados no payload

`apps/decks/tests/test_soft_delete_lifecycle.py` (10 testes novos) + helpers `read_raw_document`/`backdate_deleted_at` em `conftest.py`. Suíte completa: 53/53 testes Django passando.

## 8. Documentação

- [x] 8.1 Atualizar `PRD.md` (Sprint 6) marcando as tarefas concluídas
- [x] 8.2 Atualizar `CHANGELOG.md` com a entrada `[Sprint 6]`
- [x] 8.3 Marcar o item "Cascade delete de CardReview" em `PRD.md` §7.1 como resolvido (já feito na formalização, conferido consistente)
