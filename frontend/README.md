# Frontend

SPA React (Vite), consumindo a API do Django (`/api/v1/...`). Ver Sprint 3
do [PRD.md](../PRD.md), `<frontend>` em [PROMPT_REFINADO.md](../PROMPT_REFINADO.md)
e `openspec/changes/sprint-3-frontend-base-home-dashboard/`.

## Como rodar

```bash
make frontend-install   # ou: cd frontend && npm install
make frontend-dev       # ou: cd frontend && npm run dev
```

Abre em `http://localhost:5173`. A API do Django precisa estar rodando
(`make up` na raiz do projeto) em `http://localhost:8000`.

Por padrão a SPA aponta para `http://localhost:8000/api/v1`. Copie
`.env.example` para `.env.local` e ajuste (`VITE_API_BASE_URL`,
`VITE_GOOGLE_CLIENT_ID`):

```bash
cp .env.example .env.local
```

## Autenticação

### Login com e-mail e senha (tela real, funciona já)

`/login` tem um formulário de e-mail/senha (POST em `/auth/login/`, via
`dj_rest_auth.views.LoginView`) que já funciona de ponta a ponta, sem
depender de nenhuma credencial do Google. Use um dos usuários seedados:

```bash
poetry -C django run python manage.py seed_decks --reset
# ou: make seed
```

Qualquer usuário seedado (ex.: `seed_ana@seed.local`) tem a senha
**`anki12345`**. Só login — cadastro de conta nova e vínculo com conta
Google pelo mesmo e-mail ainda não estão implementados (backlog de
refinamento, PRD.md 7.1).

### Login com Google (tela real)

`/login` usa o Google Identity Services (fluxo OAuth2 "token client", que
devolve um `access_token` — não o botão de "Sign In" mais novo, que
devolve um ID token incompatível com o `GoogleOAuth2Adapter` do backend).
Depende de `VITE_GOOGLE_CLIENT_ID` (frontend) **e** de
`GOOGLE_OAUTH_CLIENT_ID`/`GOOGLE_OAUTH_CLIENT_SECRET` reais no
`django/.env` (backend) — nenhum dos dois está configurado ainda (mesma
pendência desde a Sprint 1: criar um projeto OAuth no
[Google Cloud Console](https://console.cloud.google.com/)). Sem isso, a
tela de login mostra uma mensagem em vez do botão.

A SPA guarda `access` **e** `refresh` token; num 401, tenta renovar
automaticamente via `/auth/token/refresh/` antes de repetir a chamada — só
desloga (evento `auth:session-expired`, redireciona pra `/login`) se o
refresh também falhar. Ver `src/api/client.js`.

### Fluxo manual via shell (alternativa ao login por e-mail/senha)

Com o login por e-mail/senha (acima) isso não é mais necessário no dia a
dia — mas ainda é útil pra gerar um token sem passar pela tela, ou pra
testar qualquer usuário sem senha conhecida:

```bash
poetry -C django run python manage.py shell -c "
from rest_framework_simplejwt.tokens import RefreshToken
from apps.accounts.models import User
user = User.objects.get(username='seed_ana')  # ou outro usuário seedado
token = RefreshToken.for_user(user)
print('access:', str(token.access_token))
print('refresh:', str(token))
"
```

Copie os dois valores impressos e, no console do navegador (com a SPA
aberta):

```js
localStorage.setItem("anki_generator_access_token", "<access colado aqui>")
localStorage.setItem("anki_generator_refresh_token", "<refresh colado aqui>")
```

Dê refresh na página. Só colar o `access` também funciona (skip o
`refresh_token`), mas aí o refresh automático não tem o que usar quando o
access expirar (1h) — a sessão simplesmente encerra e redireciona pra
`/login`, em vez de renovar sozinha.

Pra ter dados reais na Home (decks/cards/reviews), rode o seed antes:

```bash
poetry -C django run python manage.py seed_decks --reset
# ou: make seed
```

## Tokens de design

`src/tokens/` — `tokens.js`/`tokens.css` (valores), `AUDIT.md` (de onde
cada valor veio, extraído de `refs/Ashley_files/style.css`), `VISUAL_AUDIT.md`
(checklist de consistência executado contra o código).
