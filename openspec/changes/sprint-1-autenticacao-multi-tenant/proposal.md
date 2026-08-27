## Why

A Sprint 0 entregou a fundação de arquitetura (Django + domínio + infraestrutura), mas nenhuma funcionalidade real usa isso ainda — não há autenticação, não há isolamento entre usuários/tenants, e não há proteção de taxa nas APIs. Nenhuma feature de produto (decks, IA, WhatsApp, relatórios) pode avançar com segurança sem essa base, conforme `<instrucoes_de_execucao>` de `PROMPT_REFINADO.md`: multi-tenant e permissões vêm antes de qualquer outra coisa, e "NUNCA pular etapas de segurança em nome de velocidade de entrega".

## What Changes

- Model de usuário do Django estendido com `email` como campo único (chave de autenticação alternativa), reaproveitando o model nativo — não um model paralelo.
- Autenticação via Google OAuth.
- Isolamento multi-tenant obrigatório: mixin/base de queryset que filtra por tenant em toda consulta, auditável antes de qualquer endpoint ser considerado pronto.
- Autorização construída sobre `Permission`/`Group` nativos do Django — sem sistema de permissões paralelo.
- Model/mixin de auditoria (`created_at`, `created_by`, `updated_at`, `updated_by`), preenchido automaticamente pelos serializers a partir da request autenticada.
- Rate limiting de 3 req/s por usuário/cliente (valor já decidido em `PROMPT_REFINADO.md`).
- Cache (Redis) do token de autenticação, evitando reautenticação enquanto válido.
- **Primeira infraestrutura de testes automatizados do projeto**: pytest + pytest-django, com testes cobrindo as tarefas acima — escritos ao final, depois das tarefas de feature (convenção já registrada, não é TDD).

## Capabilities

### New Capabilities

- `user-identity-and-tenancy`: model de usuário (email único) + isolamento multi-tenant obrigatório via mixin de queryset, auditável em toda query/endpoint.
- `google-oauth-authentication`: login via Google OAuth e cache do token de autenticação em Redis enquanto válido.
- `authorization-permissions`: autorização via `Permission`/`Group` nativos do Django, sem sistema paralelo.
- `audit-trail`: model/mixin de auditoria (`created_at/by`, `updated_at/by`), preenchido automaticamente pelos serializers.
- `api-rate-limiting`: throttling de 3 req/s por usuário/cliente nas APIs do Django.
- `testing-foundation`: pytest + pytest-django configurados; primeiros testes automatizados do projeto, cobrindo isolamento multi-tenant e rate limiting.

### Modified Capabilities

_(nenhuma — não há specs arquivadas em `openspec/specs/` ainda; a change da Sprint 0 não foi arquivada)_

## Impact

- **Código afetado**: `django/core/settings/base.py` (AUTH_USER_MODEL, REST_FRAMEWORK throttle/cache settings), `django/core/urls.py` (rotas de auth), `django/apps/` (nova app de usuários/tenancy, ex. `apps/accounts/`), `apps/decks` (queryset/permissions passam a herdar do mixin multi-tenant quando a Sprint 2 criar os primeiros models reais).
- **Dependências novas**: `django-allauth` ou `social-auth-app-django` (Google OAuth — decisão de biblioteca fica para o design), `djangorestframework-simplejwt` ou sessão padrão do DRF (decisão de estratégia de auth fica para o design), `pytest`, `pytest-django`.
- **Banco relacional (Postgres)**: primeira migration real de `auth`/usuário customizado — ponto de atenção, mudar `AUTH_USER_MODEL` depois de migrations aplicadas em produção é custoso; esta é a primeira e única janela segura para isso.
- **Aprendizado guiado**: decisões de arquitetura desta sprint com trade-off real (estratégia de sessão vs. token, biblioteca de OAuth, desenho do isolamento multi-tenant) são conduzidas com apoio da skill `backend-mentor`, conforme `<instrucoes_de_execucao>` item 7 de `PROMPT_REFINADO.md`.
- **Fora de escopo**: CRUD de decks/cards (Sprint 2), qualquer tela de frontend (Sprint 3), agente de IA/WhatsApp/relatórios (Sprints 5–7).
