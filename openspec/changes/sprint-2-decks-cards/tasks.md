## 1. Domínio: novas entidades e campos

- [x] 1.1 Criar entidade `Category` (dataclass) em `apps/decks/domain/entities/category.py` — `id`, `owner_id`, `name`, `created_at`, `updated_at`
- [x] 1.2 Adicionar `owner_id: str` a `Deck` e `Card` (obrigatório, sem default que permita string vazia)
- [x] 1.3 Adicionar `category_id: Optional[uuid.UUID]` a `Deck`
- [x] 1.4 Adicionar `tags: List[str]` a `Card` (default `[]`)
- [x] 1.5 Adicionar campos de agendamento FSRS a `Card` (`stability`, `difficulty`, `due_at`, `state`) com defaults de card nunca revisado
- [x] 1.6 Criar entidade `CardReview` — `id`, `owner_id`, `card_id`, `reviewed_at`, `rating`, campos de resultado do agendamento (novo `stability`/`difficulty`/`due_at` pós-revisão)
- [x] 1.7 Adicionar dependência `fsrs` ao `pyproject.toml` do Django (`poetry -C django add fsrs`)

## 2. Repositórios Mongo e isolamento multi-tenant

- [x] 2.1 Atualizar `CardRepository`/`DeckRepository` — todo método de leitura/escrita exige `owner_id` no filtro. Métodos auxiliares mantidos para IA foram renomeados na Sprint 7 para `find_by_front`/`find_similar_cards`/`find_duplicates`/`exists_by_front`.
- [x] 2.2 Criar `CategoryRepository` seguindo o mesmo padrão (owner_id obrigatório desde o primeiro método)
- [x] 2.3 Criar `CardReviewRepository` (mesmo padrão) — inclui método para listar reviews de um card, escopado por owner
- [x] 2.4 Criar método de repositório para "cards devidos" (`due_at <= now`), escopado por `owner_id`
- [x] 2.5 Criar índices Mongo: composto `{owner_id, deck_id}` em `cards`, `{owner_id, category_id}` em `decks`, índice em `tags` (cards), índice em `owner_id` isolado em `categories`/`card_reviews` — `MongoDBConnectionManager.create_indexes()` refatorado para ler de `IndexDefinitions` (fonte única), em vez de manter uma segunda lista hardcoded divergente
- [x] 2.6 Teste de integração (Mongo real, não mock): tentativa de acesso cross-tenant por ID é bloqueada em `Deck`/`Category`/`Card`/`CardReview` — `apps/decks/tests/test_multi_tenant_isolation.py`
- [x] 2.7 Corrigir vínculo do Motor ao event loop — solução inicial de reconexão substituída na Sprint 7 por loop persistente e lock de conexão, validada sob requests concorrentes.

## 3. Repetição espaçada (FSRS)

- [x] 3.1 Implementar serviço de domínio que envolve o pacote `fsrs` — `domain/services/scheduling_service.py`, recebe `Card` + rating, devolve os novos campos de agendamento
- [x] 3.2 Integrar o serviço ao fluxo de registro de revisão (grava `CardReview` + atualiza `Card` com o novo agendamento, na mesma operação) — `CardReviewView`

## 4. Endpoints REST versionados (`/api/v1/`)

- [x] 4.1 Criar `DeckSerializer`/`CategorySerializer`/`CardSerializer` como `serializers.Serializer` manuais, com `create()`/`update()` delegando ao repositório correspondente
- [x] 4.2 Criar Generic Views (`ListCreateAPIView`/`RetrieveUpdateDestroyAPIView`) para `Deck`, `Category` e `Card`, com `get_queryset()` retornando lista resolvida pela ponte assíncrona persistente
- [x] 4.3 Criar `APIView` dedicada para `POST /api/v1/cards/{id}/review/` (dispara o serviço de agendamento FSRS + grava `CardReview`)
- [x] 4.4 Criar `apps/decks/urls.py` versionado e registrar em `core/urls.py`
- [x] 4.5 Aplicar isolamento multi-tenant em todas as views (owner sempre vem de `request.user`, nunca aceito como input do cliente) — validado com request HTTP real de um segundo usuário (404, não 403)

## 5. Management command de seed

- [x] 5.1 Criar comando `seed_decks` com entrypoint `asyncio.run`, usando `asyncio.gather` para inserções concorrentes independentes
- [x] 5.2 Gerar múltiplos usuários/tenants, decks/categorias variadas por usuário, cards com tags
- [x] 5.3 Gerar `CardReview` com datas passadas/recentes/futuras e ratings variados por card
- [x] 5.4 Implementar guarda contra execução em produção (checagem de `settings.DEBUG` antes de qualquer escrita)
- [x] 5.5 Implementar suporte a `--reset` (limpa dados seedados anteriormente antes de recriar) — validado: contagem de decks/cards idêntica antes/depois do reset

## 6. Testes automatizados (ao final, cobrindo as tarefas 1–5)

- [x] 6.1 Teste: `owner_id` é obrigatório e aplicado em toda query de `Deck`/`Category`/`Card`/`CardReview` (cross-tenant bloqueado) — `test_multi_tenant_isolation.py`
- [x] 6.2 Teste: CRUD dos endpoints de `Deck`/`Category`/`Card` (criação, leitura, atualização, remoção, paginação) — `test_crud_api.py`
- [x] 6.3 Teste: `POST /cards/{id}/review/` atualiza corretamente o agendamento FSRS e cria um `CardReview` — `test_review_scheduling.py`
- [x] 6.4 Teste: consulta de "cards devidos" retorna apenas cards do usuário correto com `due_at` vencido — `test_review_scheduling.py`
- [x] 6.5 Teste: comando de seed recusa rodar com configuração de produção ativa — `test_seed_command.py` (nota: `pytest-django` já força `DEBUG=False` por padrão em todos os testes, então este teste também confirma o comportamento default do plugin, não só um override artificial)
- [x] 6.6 Teste: comando de seed com `--reset` não duplica dados numa segunda execução — `test_seed_command.py`

**28/28 testes passando** (`poetry -C django run pytest apps/accounts apps/decks`) — 12 da Sprint 1 + 16 novos.

## 7. Documentação

- [x] 7.1 Atualizar `PROMPT_REFINADO.md` (`<decisoes_resolvidas>`) com as decisões desta sprint (D1–D6 de `design.md`)
- [x] 7.2 Atualizar `PRD.md` (Sprint 2) marcando as tarefas concluídas
- [x] 7.3 Atualizar `CHANGELOG.md` com a entrada `[Sprint 2]`
- [x] 7.4 Atualizar `README.md` (arquitetura, stack, roadmap) refletindo os endpoints de deck/card/category e o diagrama Mermaid
