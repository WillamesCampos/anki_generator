## 1. Model de usuário e app base

- [x] 1.1 Criar app `django/apps/accounts/` com model de usuário customizado estendendo `AbstractUser`, com `email` único
- [x] 1.2 Definir `AUTH_USER_MODEL = "accounts.User"` em `django/core/settings/base.py` — antes de qualquer outra migration real
- [x] 1.3 Gerar e aplicar a migration inicial do model de usuário customizado — validado contra Postgres real (volume de dev resetado, sem dados reais em jogo)

## 2. Autenticação (JWT + Google OAuth) — mentorado, explicar cada peça durante a implementação

- [x] 2.1 Instalar `djangorestframework-simplejwt`, `django-allauth`, `dj-rest-auth` (+ `requests`, `cryptography`, dependências transitivas não declaradas)
- [x] 2.2 Configurar `simplejwt` (access token 15min, refresh token 7 dias) em `django/core/settings/base.py`
- [x] 2.3 Configurar `django-allauth` para o provedor Google (client ID/secret via variável de ambiente, nunca hardcoded)
- [x] 2.4 Configurar `dj-rest-auth` (+ `dj_rest_auth.registration`) para expor o fluxo social como endpoints REST, com `USE_JWT = True`
- [x] 2.5 Implementar blocklist de refresh token no Redis — validado end-to-end via HTTP real (refresh funciona antes do logout, 401 depois)
- [x] 2.6 Montar as rotas de auth em `django/core/urls.py`, versionadas (`/api/v1/auth/google/`, `/token/refresh/`, `/logout/`)
- [x] 2.7 Validar o fluxo manualmente — **parcial**: JWT/refresh/logout/blocklist validados de ponta a ponta com tokens gerados diretamente; o handshake real com o Google **não** foi validado (requer `GOOGLE_OAUTH_CLIENT_ID`/`SECRET` reais de um projeto no Google Cloud Console, que o usuário ainda precisa criar)

## 3. Multi-tenant e autorização

- [x] 3.1 Implementar mixin de queryset/manager que filtra por usuário dono (`TenantOwnedModel`/`TenantOwnedQuerySet` em `apps/accounts/tenancy.py`) — testado com modelo descartável de teste, incluindo tentativa de acesso cross-tenant por ID
- [x] 3.2 Confirmar que nenhuma entidade `Tenant`/`Organization` foi introduzida (ver D3 em `design.md`)
- [x] 3.3 Configurar autorização via `Permission`/`Group` nativos do Django — validado que o mecanismo nativo continua funcionando com o `User` customizado (troca de `AUTH_USER_MODEL` não quebrou `has_perm`/`Group`)

## 4. Auditoria

- [x] 4.1 Criar `AuditMixin` abstrato (`created_at`, `created_by`, `updated_at`, `updated_by`), campos opcionais no banco
- [x] 4.2 Implementar preenchimento automático de `created_by`/`updated_by` no serializer (`AuditSerializerMixin`), ignorando qualquer valor enviado pelo cliente — testado explicitamente com tentativa de injeção de `created_by` pelo cliente

## 5. Rate limiting

- [x] 5.1 Configurar `DEFAULT_THROTTLE_CLASSES`/`DEFAULT_THROTTLE_RATES` do DRF para 3 req/s, usando o Redis já configurado — validado com burst real (3 requests OK, 4ª+ recebem 429)

## 6. Testes automatizados (ao final, cobrindo as tarefas 1–5)

- [x] 6.1 Configurar pytest + pytest-django (`pyproject.toml`)
- [x] 6.2 Teste: e-mail duplicado é rejeitado na criação de usuário
- [x] 6.3 Teste: tentativa de acesso cross-tenant (por ID, de outro usuário) é bloqueada
- [x] 6.4 Teste: requests acima de 3 req/s recebem 429
- [x] 6.5 Teste: `created_by`/`updated_by` são preenchidos automaticamente e ignoram valor enviado pelo cliente
- [x] 6.6 Teste: logout revoga o refresh token (tentativa de uso após logout falha)
- [x] 6.7 (adicional) Teste: `Permission`/`Group` nativos funcionam com o `User` customizado

**12/12 testes passando** (`poetry -C django run pytest apps/accounts`).

## 7. Documentação

- [x] 7.1 Atualizar `PRD.md` (Sprint 1) marcando as tarefas concluídas
- [x] 7.2 Registrar entrada no `CHANGELOG.md`
