## Context

Levantamento feito em sessão de mentoria técnica, com o código em mãos (não é decisão especulativa):

- `grep -rn "asyncio.gather" apps/decks` só encontra uso em `management/commands/seed_decks.py` — nenhuma view ou repositório do caminho de requisição real faz fan-out concorrente de queries Mongo. O assincronismo do Motor não é aproveitado onde importaria (o request/response da API).
- `apps/decks/infrastructure/async_bridge.py` (`PersistentAsyncExecutor`) existe só para permitir que views/serializers/tasks síncronos do Django cheguem a repositórios `async def`: mantém uma thread daemon dedicada rodando um único event loop pro processo, e usa `run_coroutine_threadsafe` + `future.result()` para bloquear a thread chamadora até o resultado voltar.
- `apps/decks/infrastructure/mongodb_connection.py` (`MongoDBConnectionManager`) rastreia qual event loop criou o `AsyncIOMotorClient` (`self._loop`) porque o Motor amarra sua pool de conexões ao loop ativo no momento da criação; `is_connected()` compara `current_loop is self._loop` pra forçar reconexão se o loop mudou (ex.: a thread do bridge morreu e foi recriada); `ensure_mongodb_connection()` mantém um `asyncio.Lock` que também precisa ser recriado por loop, pelo mesmo motivo.
- `pymongo` já é dependência direta (`django/pyproject.toml`), tipicamente puxado como transitiva do Motor mas já pinada explicitamente. `pymongo.MongoClient` é thread-safe nativamente e não tem nenhuma noção de event loop — elimina inteiramente a classe de bug "objeto asyncio amarrado ao loop errado".
- Django continua servido via `manage.py runserver` (WSGI, confirmado em `entrypoint.sh`) — decisão já tomada de não migrar para ASGI. Os microsserviços FastAPI (ex. `document-generator`) continuam com `uvicorn`/asyncio nativo, sem relação com esta mudança.
- Investigado: `apps/decks/domain/services/duplicate_detection_service.py` é um serviço de leitura-e-cálculo (busca cards existentes, calcula similaridade) — não é um guard atômico de "verifica duplicata, então insere" na mesma transação. Não há, portanto, evidência de que a serialização implícita do event loop único garantisse atomicidade que a migração para múltiplas threads (pymongo sob WSGI multi-thread) removeria. Essa investigação cobriu esse serviço especificamente; vale revisão adicional durante a migração dos repositórios (ver Risks).
- Investigado: `mongodb_manager.health_check()` e `get_database_info()` não são chamados por nenhuma view, comando ou teste (`grep` confirmado) — código morto hoje, não exposto por nenhum endpoint. Fica como decisão em aberto (ver Open Questions), não parte obrigatória desta migração.

## Goals / Non-Goals

**Goals:**
- Remover `async_bridge.py` e toda a lógica de rastreamento/comparação de event loop em `mongodb_connection.py`.
- Preservar 100% do comportamento observável: filtros por `owner_id`, soft delete, paginação, criação de índices, contratos de request/response da API REST — nenhuma regra de negócio muda, só o mecanismo de I/O.
- Suíte de testes existente (Mongo real, sem mocks, convenção já estabelecida no projeto) passa sem alteração de asserções — só a forma de invocar repositórios (sem `await`/`asyncio.run`).
- `seed_decks.py` mantém desempenho aceitável para uso local/CI via operações em lote do pymongo, mesmo perdendo o paralelismo de `asyncio.gather`.

**Non-Goals:**
- Migrar Django para ASGI — decisão já tomada de manter WSGI; fora de escopo completamente.
- Mudar o schema dos documentos no MongoDB ou qualquer regra de negócio de `decks`/`cards`/`categories`/`reviews`/`generation_sessions`.
- Alterar os microsserviços FastAPI (permanecem async/uvicorn).
- Adicionar `pytest-asyncio` ou qualquer suporte a teste async — deixa de ser necessário, não passa a ser necessário em outro lugar.

## Decisions

### D1 — Manter `MongoDBConnectionManager` como Singleton fino, só remover a parte de event loop
Duas opções: (a) manter um manager central (Singleton), agora sem nenhum rastreamento de loop — vira lazy-connect simples protegido por `threading.Lock`; ou (b) eliminar o manager por completo e usar um `pymongo.MongoClient` de módulo diretamente em cada repositório.

Escolhido (a). Motivo: o manager já centraliza configuração via `MongoDBConfig.from_env()`, criação de índices (`create_indexes()`, usada pelos testes/seed a partir de `IndexDefinitions`) e é o ponto único que `ensure_mongodb_connection()` (chamado no início de todo método de repositório) usa para garantir conexão estabelecida. Migrar pra (b) obrigaria reescrever esse ponto de entrada em 5 repositórios + testes + seed, por um ganho de simplicidade marginal — o `MongoClient` do pymongo já faz lazy-connect e pooling sozinho, então o manager vira principalmente um wrapper de configuração/índices, não uma peça de gerência de conexão complexa como era antes.
- **Alternativa descartada**: (b), client de módulo direto. Rejeitada por aumentar o diff desta migração sem necessidade — pode ser revisitada depois, isoladamente, como uma simplificação própria se o manager continuar parecendo redundante na prática.

### D2 — Substituir `await cursor.to_list(...)`/`async for` por iteração direta do cursor pymongo
Cursor do pymongo é iterável diretamente (`for doc in collection.find(...)`) ou materializável com `list(cursor)` — sem contraparte a `await`. Mudança mecânica, aplicada em todos os repositórios; não há alternativa real a avaliar aqui.

### D3 — `seed_decks.py`: trocar `asyncio.gather` por operação em lote (`insert_many`/`bulk_write`), não por loop sequencial puro
O ganho do `gather` original era paralelizar round-trips de rede entre vários inserts independentes. Um loop sequencial simples (um `insert_one` por vez) perderia esse ganho por completo — cada seed de deck com muitos cards pagaria N round-trips sequenciais. `insert_many`/`bulk_write` do pymongo é o equivalente síncrono correto: agrupa múltiplos documentos numa única operação de rede, sem precisar de concorrência real para isso.
- **Alternativa descartada**: loop sequencial `insert_one` por documento. Rejeitada — desempenho pior sem necessidade, quando o pymongo já oferece a operação em lote nativa para exatamente esse caso.

## Risks / Trade-offs

- **[Risco]** Diferença sutil entre cursor async (`to_list`, materializado explicitamente) e cursor sync (iterável, pode ser esgotado uma única vez se não materializado em lista) pode introduzir bug onde um cursor é iterado duas vezes silenciosamente e a segunda vez volta vazio. → **Mitigação**: migrar e testar um repositório por vez (não tudo de uma vez), rodando a suíte real de testes (Mongo real, sem mock) a cada repositório, antes de seguir para o próximo.
- **[Risco]** Alguma suposição implícita de serialização de acesso que o loop único do bridge pudesse estar garantindo "de graça" deixa de existir sob múltiplas threads reais do WSGI. → **Mitigação**: investigação já feita em `duplicate_detection_service.py` não encontrou dependência desse tipo (é leitura-e-cálculo, não check-then-write atômico); revisar os 5 repositórios durante a migração em busca do mesmo padrão antes de considerar o risco fechado.
- **[Risco]** Nomes/formatos de kwargs de conexão (`ssl`, `ssl_cert_reqs`, pool sizes) em `mongodb_config.py` podem divergir sutilmente entre `AsyncIOMotorClient` e `pymongo.MongoClient`, mesmo o Motor sendo uma casca fina sobre o pymongo por baixo. → **Mitigação**: primeiro passo da migração é só trocar o client em `mongodb_connection.py` e validar `_test_connection()` (ping real) antes de tocar em qualquer repositório.
- **[Risco]** `seed_decks.py`/`migrate_card_fields.py` são scripts usados manualmente/CI — reescrever a lógica de bulk pode mudar sutilmente mensagens de log/contagem exibidas ao usuário. → **Mitigação**: comparar saída do comando antes/depois manualmente num ambiente local com Mongo de teste, não só depender da suíte automatizada (que não cobre esses comandos hoje).

## Migration Plan

Sem migração de dados (mesmo MongoDB, mesmos documentos, nenhuma mudança de schema) — é troca de driver, não de armazenamento. Sequência seguindo o princípio de menor lote possível por passo, com a suíte de testes real (Mongo via `docker compose up -d mongo`) rodando a cada passo:

1. `mongodb_config.py` + `mongodb_connection.py`: trocar `AsyncIOMotorClient` por `pymongo.MongoClient`, remover rastreamento de loop, `ensure_mongodb_connection()` vira função síncrona com `threading.Lock`. Validar conexão isoladamente (ping) antes de seguir.
2. Migrar as 5 interfaces de domínio (`I*Repository`) para métodos síncronos.
3. Migrar os 5 repositórios concretos, um de cada vez, rodando a suíte de testes de `apps/decks` a cada um.
4. Migrar `duplicate_detection_service.py` (métodos síncronos).
5. Atualizar `views.py` e `serializers.py`: remover `persistent_async_to_sync`/`async_to_sync`, chamar repositórios diretamente.
6. Atualizar `tasks.py` (Celery `purge_soft_deleted`).
7. Reescrever `seed_decks.py` e `migrate_card_fields.py` (bulk write, sem `gather`).
8. Simplificar `tests/conftest.py` (remover `run_async`/`asyncio.run`); decidir o destino de `test_mongodb_integration.py` (ver Open Questions).
9. Deletar `async_bridge.py`; remover `motor` de `pyproject.toml`; rodar suíte completa uma última vez.

**Rollback**: mudança inteira vive numa branch de feature (`refactor/motor-para-pymongo`) sem tocar dado em produção — rollback é simplesmente não fazer merge, ou reverter o(s) commit(s). Não há passo irreversível (sem migração de schema, sem alteração de documentos existentes).

## Open Questions

- `mongodb_manager.health_check()`/`get_database_info()` são código morto hoje (não chamados por nenhuma view/comando/teste). Migrar mesmo assim (mecânico) ou remover como parte desta change, já que o arquivo inteiro está sendo reescrito? Fica para decisão no início da implementação, não bloqueia o restante do plano.
- `test_mongodb_integration.py` (script standalone, hoje excluído da coleta do pytest via `collect_ignore` por ser `async def` de nível de módulo): reescrever como script síncrono, converter em teste pytest de verdade, ou arquivar/remover? Avaliar se ainda tem valor distinto da suíte de testes normal de `apps/decks/tests/`.
