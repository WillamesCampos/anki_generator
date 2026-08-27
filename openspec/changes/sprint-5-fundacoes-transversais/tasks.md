## 1. Auditoria — entidades de domínio

- [x] 1.1 Adicionar `created_by: Optional[str]` e `updated_by: Optional[str]` em `Deck`, `Card`, `Category`, `CardReview` (`apps/decks/domain/entities/*.py`) — `to_dict()`/`from_dict()` atualizados
- [x] 1.2 Atualizar `apps/decks/infrastructure/schemas.py` (to_document/from_document das 4 entidades) para persistir os campos novos no Mongo
- [x] 1.3 `apps/decks/serializers.py`: `create()`/`update()` de cada serializer preenche `created_by`/`updated_by` a partir de `self.context["request"].user`, nunca aceito do payload — mesmo padrão já usado por `owner_id`

## 2. Autorização — grupo e permission class

- [x] 2.1 `Group.objects.get_or_create(name="standard_user")` — idempotente, criado numa migration de dados de `apps/accounts/`
- [x] 2.2 Todo novo usuário (Google, e-mail/senha, seed) entra automaticamente no grupo `standard_user` — hook no signup e em `seed_decks.py` (implementado via `post_save` signal em `User`, cobre `get_or_create` do seed e qualquer fluxo futuro de criação sem hook por-view)
- [x] 2.3 `permission_classes` customizado (`apps/decks/permissions.py` ou equivalente) verificando pertencimento ao grupo, substituindo `IsAuthenticated` puro em `CategoryListCreateView`, `CategoryDetailView`, `DeckListCreateView`, `DeckDetailView`, `CardListCreateView`, `CardDetailView`, `CardReviewView`, `CardReviewListView`

## 3. Autenticação service-to-service (JWT)

- [x] 3.1 Django: função de emissão do JWT de serviço (HS256) — claims `iss` (nome do serviço chamador), `aud` (`document-generator`), `exp` curto (30-60s), header `kid` identificando a chave usada; segredo(s) via variável de ambiente própria (`SERVICE_JWT_KEYS` ou equivalente), separada de `SIMPLE_JWT`/`DJANGO_SECRET_KEY` (`core/service_auth.py`)
- [x] 3.2 Django: cliente HTTP que chama `document-generator` passa a assinar e anexar o token (`Authorization: Bearer <jwt>`) em toda request (`core/service_clients.py`, `call_document_generator` — pronto pra Sprint 9 importar)
- [x] 3.3 `document-generator` (FastAPI): dependency/middleware que verifica assinatura, `aud`, `exp` e `kid` localmente (sem chamar o Django de volta) — mapa local `{kid: secret}` via env var própria, aceitando qualquer `kid` presente no mapa, não só o mais recente; requests sem token válido recebem 401 (`app/auth.py`, aplicado ao router de `decks` via `Depends`)
- [x] 3.4 Documentar no `.env.example` de cada lado (`django/`, `microservices/document-generator/`) as variáveis novas e o procedimento de rotação (adicionar chave nova → redeploy → promover a ativa → remover a antiga → redeploy) — `django/.env` (sem `.env.example` prévio no projeto) e `microservices/document-generator/config.example.env` (tracked)

## 4. Testes automatizados

- [x] 4.1 `created_by`/`updated_by` preenchidos corretamente em create/update de cada entidade (`apps/decks/tests/test_audit_trail.py`)
- [x] 4.2 Campos `created_by`/`updated_by` enviados pelo cliente no payload são ignorados (nunca sobrescrevem o valor real) (`test_audit_trail.py::test_deck_create_ignores_client_supplied_audit_fields`)
- [x] 4.3 Grupo `standard_user` atribuído automaticamente em cada fluxo de criação de usuário (signup Google, signup e-mail/senha, seed) (`apps/accounts/tests/test_groups.py` — cobre `create_user` e `get_or_create`, caminho usado pelo seed)
- [x] 4.4 Usuário autenticado sem grupo autorizado é negado nos endpoints de decks/cards (distinto de 401 não-autenticado) (`apps/decks/tests/test_authorization.py`)
- [x] 4.5 `document-generator` rejeita chamada sem JWT de serviço, com JWT expirado e com `kid` desconhecido (401 nos três casos); aceita chamada com JWT válido (`microservices/document-generator/tests/test_service_auth.py`)
- [x] 4.6 Cenário de rotação: token assinado com a chave antiga ainda é aceito enquanto ela está no mapa do verificador; deixa de ser aceito depois de removida (`test_service_auth.py::test_rotation_window_accepts_both_old_and_new_key`, `::test_removed_key_is_rejected_after_rotation`)

Suíte completa: 43/43 testes Django (`poetry run pytest apps/`) + 9/9 testes FastAPI (`docker compose run --rm --entrypoint "python -m pytest tests/ -v" document-generator`), todos passando.

## 5. Documentação

- [x] 5.1 Atualizar `PRD.md` (Sprint 5) marcando as tarefas concluídas
- [x] 5.2 Atualizar `CHANGELOG.md` com a entrada `[Sprint 5]`
