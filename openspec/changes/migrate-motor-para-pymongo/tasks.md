## 1. Camada de conexão

- [x] 1.1 Trocar `AsyncIOMotorClient` por `pymongo.MongoClient` em `apps/decks/infrastructure/mongodb_connection.py`
- [x] 1.2 Remover `self._loop`, `is_connected()` baseado em comparação de event loop, e todo `import asyncio` associado
- [x] 1.3 Trocar o `asyncio.Lock` por-loop de `ensure_mongodb_connection()` por um `threading.Lock` simples de escopo de módulo/instância
- [x] 1.4 `connect()`, `disconnect()`, `_test_connection()`, `get_collection()`, `create_indexes()`, `drop_collection()` viram métodos síncronos comuns (`def`, sem `await`)
- [x] 1.5 Validar manualmente a conexão (ping real contra o `mongo` do `docker-compose.yml`) antes de seguir para os repositórios
- [x] 1.6 Decidir e aplicar o destino de `health_check()`/`get_database_info()` (código morto hoje — migrar mecanicamente ou remover, ver Open Questions do design.md)

## 2. Interfaces de domínio

- [x] 2.1 `apps/decks/domain/repositories/ideck_repository.py`: métodos viram síncronos
- [x] 2.2 `apps/decks/domain/repositories/icard_repository.py`: métodos viram síncronos
- [x] 2.3 `apps/decks/domain/repositories/icard_review_repository.py`: métodos viram síncronos
- [x] 2.4 `apps/decks/domain/repositories/icategory_repository.py`: métodos viram síncronos
- [x] 2.5 `apps/decks/domain/repositories/igeneration_session_repository.py`: métodos viram síncronos

## 3. Repositórios concretos (um por vez, com testes reais a cada passo)

- [x] 3.1 Migrar `apps/decks/infrastructure/repositories/deck_repository.py` (trocar `await cursor.to_list()`/`async for` por iteração/`list()` direta do cursor pymongo) e rodar a suíte de testes de decks
- [x] 3.2 Migrar `apps/decks/infrastructure/repositories/card_repository.py` e rodar a suíte de testes de cards
- [x] 3.3 Migrar `apps/decks/infrastructure/repositories/category_repository.py` e rodar a suíte de testes de categories
- [x] 3.4 Migrar `apps/decks/infrastructure/repositories/card_review_repository.py` e rodar a suíte de testes de reviews
- [x] 3.5 Migrar `apps/decks/infrastructure/repositories/generation_session_repository.py` e rodar a suíte de testes correspondente

## 4. Serviços de domínio

- [x] 4.1 `apps/decks/domain/services/duplicate_detection_service.py`: métodos viram síncronos (`find_duplicates_for_card`, `find_exact_duplicates`, `find_similar_fronts`, `_get_all_cards`)

## 5. Camada web (views e serializers)

- [x] 5.1 `apps/decks/views.py`: remover todos os call sites de `persistent_async_to_sync`/`async_to_sync`, chamar repositórios diretamente
- [x] 5.2 `apps/decks/serializers.py`: remover todos os call sites de `async_to_sync` (create/update de Category, Deck, Card)
- [x] 5.3 Testar manualmente (ou via suíte) os endpoints principais de decks/cards/categories/reviews via `APIClient`

## 6. Celery

- [x] 6.1 `apps/decks/tasks.py`: `purge_soft_deleted` chama os repositórios diretamente, sem ponte
- [x] 6.2 Validar a task rodando localmente contra o worker Celery (`docker compose run celery-worker` ou equivalente)

## 7. Management commands

- [x] 7.1 `apps/decks/management/commands/seed_decks.py`: substituir `asyncio.gather` por `insert_many`/`bulk_write` síncrono do pymongo, preservando o conjunto final de documentos gerados
- [x] 7.2 `apps/decks/management/commands/migrate_card_fields.py`: converter para API síncrona do pymongo
- [x] 7.3 Rodar os dois comandos manualmente contra um Mongo local e comparar saída/contagens com o comportamento anterior

## 8. Testes

- [x] 8.1 `apps/decks/tests/conftest.py`: remover `run_async`/`asyncio.run` e simplificar fixtures para chamadas síncronas diretas
- [x] 8.2 Decidir o destino de `apps/decks/tests/test_mongodb_integration.py` (reescrever síncrono, converter em teste pytest real, ou remover) e aplicar
- [x] 8.3 Remover o `collect_ignore` em `conftest.py` se `test_mongodb_integration.py` deixar de ser um script `async def` de nível de módulo
- [x] 8.4 Rodar a suíte completa de `apps/decks/tests/` contra Mongo real e confirmar 100% de paridade com o comportamento anterior

## 9. Limpeza final e dependências

- [x] 9.1 Deletar `apps/decks/infrastructure/async_bridge.py` por completo
- [x] 9.2 Remover a dependência `motor` de `django/pyproject.toml` (e do lockfile) — `pymongo` permanece
- [x] 9.3 `grep -rn "motor\|async_bridge\|persistent_async_to_sync" apps/decks --include="*.py"` deve retornar vazio (confirma que não sobrou nenhum resquício)
- [x] 9.4 Rodar a suíte de testes completa do projeto (não só `decks`) uma última vez, incluindo o gate de CI local se aplicável
- [x] 9.5 Atualizar `PROMPT_REFINADO.md`/documentação relevante se algum `<regra_obrigatoria>` ou decisão registrada citar Motor/async explicitamente
