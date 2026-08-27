## Context

A Sprint 0 entregou a fundação (Django 6 + DRF, PostgreSQL para auth, MongoDB para domínio de deck/card, Redis/RabbitMQ/Celery já no `docker-compose.yml`, microsserviço `document-generator`). Nenhuma feature usa Postgres ainda de verdade — a única migration aplicada até agora é o schema padrão do Django (`auth`, `admin`, `sessions`, `contenttypes`). Isso significa que **esta é a única janela segura para definir o `AUTH_USER_MODEL` customizado** — trocá-lo depois de migrations reais aplicadas em produção é uma migração dolorosa e arriscada.

O frontend (Sprint 3) será uma SPA React buildada estaticamente e hospedada em um bucket S3 — origem diferente de onde o Django roda (hoje `localhost`, depois a VPS Hostinger). Essa restrição concreta (SPA em origem separada da API) foi o principal fator nas decisões de autenticação abaixo, definidas em sessão de mentoria via `backend-mentor`.

## Goals / Non-Goals

**Goals:**
- Model de usuário customizado com `email` único, sem quebrar o restante do schema nativo do Django (`Permission`/`Group`/`auth`).
- Autenticação stateless via JWT, apropriada para a SPA em origem separada, com estratégia de revogação via Redis (não "JWT stateless puro").
- Login via Google OAuth, usando bibliotecas maduras do ecossistema (não implementação manual do fluxo OAuth2).
- Isolamento multi-tenant = isolamento por usuário (não uma entidade `Organization`/`Tenant` separada — ver D3), aplicado via mixin de queryset reutilizável.
- Autorização via `Permission`/`Group` nativos do Django.
- Model/mixin de auditoria preenchido automaticamente pelos serializers.
- Rate limiting (3 req/s) via throttle classes do DRF, usando o Redis já configurado como backend de cache.
- Primeira infraestrutura de testes automatizados do projeto (pytest + pytest-django), escrita ao final, cobrindo os itens acima.

**Non-Goals:**
- Qualquer entidade `Organization`/`Tenant` separada do `User` — decidido explicitamente que não existe necessidade real disso hoje (ver D3).
- Outros provedores de login social além do Google (Facebook, GitHub, etc.) — `django-allauth` suporta, mas não é usado agora.
- CRUD de decks/cards (Sprint 2), qualquer tela de frontend (Sprint 3), agente de IA/WhatsApp/relatórios (Sprints 5–7).
- Refresh token rotation avançado (ex.: detecção de reuse) — fica para uma revisão de segurança futura se necessário; a base (blocklist no Redis) já cobre o caso de revogação simples.

## Decisions

### D1 — Autenticação: JWT (`djangorestframework-simplejwt`) com refresh token em blocklist no Redis
Sessão de mentoria concluiu que o caso do projeto (SPA em S3, origem separada da API Django) é exatamente uma das duas justificativas legítimas para JWT em vez de sessão — a outra sendo múltiplos serviços validando token sem round-trip ao auth server. Access token de vida curta (10–15 min) + refresh token de vida mais longa, cujo estado vive no Redis (permite revogar uma sessão específica no logout ou em caso de comprometimento). Isso é a implementação concreta do que `PROMPT_REFINADO.md` já mandava ("cache para pegar o token de autenticação sem estar expirado").
- **Alternativa considerada**: sessão Django (cookie + CSRF). Rejeitada — cookie cross-origin (SPA em S3 vs. API em outro domínio) exige `SameSite=None` + `Secure` e traz fricção real de CORS/CSRF cross-origin, sem necessidade já que o caso de uso justifica JWT de forma legítima.
- **Alternativa considerada**: JWT "stateless puro", sem qualquer estado no servidor. Rejeitada — sem mecanismo de revogação, um token comprometido ou logout não têm efeito prático até a expiração natural.

### D2 — Login com Google: `django-allauth` + `dj-rest-auth` + `simplejwt`
Nunca implementar o fluxo OAuth2 na mão (superfície de segurança real: validação de `state`, verificação de assinatura, replay). `django-allauth` é a biblioteca madura e mantida do ecossistema Django para isso. Como `allauth` sozinho é orientado a templates HTML (não API REST), `dj-rest-auth` é a peça que expõe o fluxo social como endpoints REST, devolvendo o JWT do `simplejwt` no final — é a combinação padrão para "Django REST + SPA + login social".
- **Alternativa considerada**: `social-auth-app-django`. Rejeitada — manutenção mais irregular hoje que `django-allauth`.
- **Alternativa considerada**: implementar o handshake OAuth2 manualmente contra os endpoints do Google (`google-auth`/`requests-oauthlib` direto). Rejeitada — reinventar código de segurança sem necessidade; nenhum requisito do projeto exige esse nível de controle customizado.

### D3 — Multi-tenant = isolamento por usuário; nenhuma entidade `Tenant`/`Organization`
Nada em `PROMPT_REFINADO.md` ou `PRD.md` descreve organizações, times, ou hierarquia (ex.: professor gerenciando alunos) — a descrição funcional é sempre "usuário estuda os próprios decks". "Multi-tenant" aqui significa isolamento por `User`, não multi-tenancy organizacional clássica de SaaS B2B. O mixin de queryset filtra por uma FK direta (`owner`/`user`) em cada model, sem tabela de tenant intermediária.
- **Alternativa considerada**: modelar `Tenant`/`Organization` desde já, pensando em expansão futura (decks compartilhados, professor/aluno). Rejeitada — abstração prematura (YAGNI): nenhum desses cenários está no roadmap (`PRD.md`, Sprints 1–10); adicionar a camada intermediária agora custaria um JOIN extra em toda query sem benefício presente. Se esse requisito aparecer de verdade no futuro, é modelado então, com o requisito real na mão.

### D4 — Rate limiting via throttle classes do DRF
3 req/s (já decidido) implementado via `DEFAULT_THROTTLE_CLASSES`/`DEFAULT_THROTTLE_RATES` do DRF, usando o backend de cache Redis já configurado (`django/core/settings/base.py`, `CACHES["default"]`) — não uma solução customizada. É a via idiomática do framework e não introduz componente novo.

### D5 — Auditoria: mixin de model abstrato + preenchimento automático no serializer
Um `AuditMixin` abstrato (`created_at`, `created_by`, `updated_at`, `updated_by`) herdado pelos models que precisam de auditoria (a partir da Sprint 2, quando os primeiros models Django reais de produto existirem). `created_by`/`updated_by` são preenchidos no serializer a partir de `self.context["request"].user`, nunca aceitos como input do cliente.

## Risks / Trade-offs

- **[Risco]** Trocar `AUTH_USER_MODEL` depois de migrations reais aplicadas é uma migração muito custosa. → **Mitigação**: esta sprint é a única janela seguras para isso — o model customizado é criado agora, antes de qualquer dado real existir.
- **[Risco]** JWT mal configurado (tempo de expiração longo demais, ausência de blocklist) reintroduz os problemas que a sessão evita. → **Mitigação**: access token curto (10–15 min) + refresh token com estado no Redis, testado explicitamente (tarefa 1.9).
- **[Risco]** Isolamento multi-tenant mal implementado é o `<ponto_critico id="isolamento-multi-tenant">` mais grave do projeto — falha aqui é crítica/bloqueante por definição em `PROMPT_REFINADO.md`. → **Mitigação**: mixin de queryset único e reutilizável (não filtro duplicado em cada view), com teste automatizado explícito de tentativa de acesso cross-tenant (tarefa 1.9).
- **[Trade-off]** Usuário nunca usou `django-allauth`/`dj-rest-auth` antes — vai exigir explicação didática durante a implementação (não só a decisão), o que torna essa parte da sprint mais lenta que um simples "instalar e configurar". Aceito conscientemente — é objetivo de aprendizado explícito do usuário, não só de entrega.

## Migration Plan

1. Criar app `apps/accounts` com o model de usuário customizado (`email` único) — `AUTH_USER_MODEL` definido antes de qualquer outra migration real.
2. Rodar a migration inicial do model de usuário customizado (janela única seguras para isso).
3. Instalar e configurar `django-allauth` + `dj-rest-auth` + `simplejwt`, com explicação didática de cada peça durante a implementação.
4. Configurar `simplejwt` (tempos de expiração) + blocklist de refresh token no Redis.
5. Implementar o mixin de queryset multi-tenant (`apps/accounts` ou um app `core`/`common` compartilhado) — pronto para ser herdado pelos models reais da Sprint 2.
6. Configurar throttle classes do DRF (3 req/s).
7. Criar `AuditMixin` abstrato.
8. Configurar pytest + pytest-django; escrever os testes cobrindo os itens acima.
- **Rollback**: sem dados reais em produção ainda — rollback é `git revert`/descartar a branch, sem risco de perda de dados.

## Open Questions

- Tempo exato de expiração do access token e do refresh token — proposta inicial 10–15 min / 7 dias, a confirmar durante a implementação.
- Nome definitivo da app Django que hospeda usuário + multi-tenancy (`apps/accounts` é a proposta; pode ser renomeada durante a implementação se surgir nome melhor).
