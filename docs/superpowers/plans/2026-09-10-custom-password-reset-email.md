# Custom Password Reset Email Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the default django-allauth password-reset message with the approved Anki Generator “Dark premium” multipart email without changing the React reset screens or the reset-token flow.

**Architecture:** Keep `dj-rest-auth` and `AllAuthPasswordResetForm` responsible for user lookup, token generation, anti-enumeration behavior, and delivery. Add a project-level Django template directory that takes precedence over package templates, then override the allauth `account/email/password_reset_key` subject, plain-text body, and HTML body. The allauth adapter will automatically produce `EmailMultiAlternatives` when both message formats exist.

**Tech Stack:** Python 3.13, Django 6.0.8, django-allauth 65.18.0, dj-rest-auth 7.2.0, Django templates, pytest/pytest-django, Resend SMTP in production.

## Global Constraints

- Scope is exclusively the password-reset email; do not modify any React file.
- Preserve `CustomPasswordResetSerializer`, `frontend_password_reset_url_generator`, and the `/redefinir-senha?uid=...&token=...` contract.
- Preserve the same 200 response for unknown email addresses and all existing token invalidation behavior.
- Use the approved “Dark premium” direction: `#000000` page, `#161616` panel, `#ff9800` accent, white/gray text, and the textual “Anki Generator” wordmark.
- Include complete and equivalent `text/plain` and `text/html` bodies.
- Do not load external images, fonts, stylesheets, scripts, or tracking pixels.
- Use a table-based, inline-styled email layout with a maximum width of 600 px.
- The visible CTA and fallback URL must both use the existing `password_reset_url` context variable.
- Subject must render as `[Anki Generator] Redefina sua senha`, with the prefix supplied by the allauth `Site.name` configuration.

---

## File Structure

- `django/core/settings/base.py`: register the project-level template directory before app template discovery.
- `django/templates/account/email/password_reset_key_subject.txt`: provide the subject body consumed by allauth.
- `django/templates/account/email/password_reset_key_message.txt`: provide the accessible plain-text fallback.
- `django/templates/account/email/password_reset_key_message.html`: provide the approved branded HTML alternative.
- `django/apps/accounts/tests/test_password_reset_email.py`: verify template precedence and the final multipart message independently from the reset-confirmation tests.
- `django/apps/accounts/serializers.py`: update the module documentation to describe the new division of responsibilities.
- `django/apps/accounts/tests/test_password_reset.py`: remove the stale statement that the packaged allauth template is used.
- `openspec/changes/sprint-9-tela-de-estudo/proposal.md`: include the email customization in Sprint 9 impact.
- `openspec/changes/sprint-9-tela-de-estudo/tasks.md`: track the new email work as completed Sprint 9 tasks.
- `PRD.md`, `PROMPT_REFINADO.md`, `CHANGELOG.md`: replace the superseded “default template” decision with the approved custom multipart template.

---

### Task 1: Branded multipart password-reset email

**Files:**
- Create: `django/apps/accounts/tests/test_password_reset_email.py`
- Modify: `django/core/settings/base.py:74-87`
- Create: `django/templates/account/email/password_reset_key_subject.txt`
- Create: `django/templates/account/email/password_reset_key_message.txt`
- Create: `django/templates/account/email/password_reset_key_message.html`

**Interfaces:**
- Consumes: allauth template prefix `account/email/password_reset_key` and context variable `password_reset_url: str` produced by `AllAuthPasswordResetForm.save()`.
- Produces: one `EmailMultiAlternatives` message whose primary body is `text/plain` and whose single alternative has MIME type `text/html`.

- [ ] **Step 1: Write the failing integration test**

Create `django/apps/accounts/tests/test_password_reset_email.py`:

```python
import re
from html import escape

import pytest
from django.core import mail
from rest_framework.test import APIClient

from apps.accounts.models import User

RESET_URL_PATTERN = re.compile(
    r"http://localhost:5173/redefinir-senha\?uid=[\w-]+&token=[\w.%+-]+"
)


@pytest.mark.django_db
def test_password_reset_email_uses_branded_multipart_templates():
    User.objects.create_user(
        username="branded-reset",
        email="branded-reset@example.com",
        password="senha-antiga-123",
    )

    response = APIClient().post(
        "/api/v1/auth/password/reset/",
        {"email": "branded-reset@example.com"},
        format="json",
    )

    assert response.status_code == 200
    assert len(mail.outbox) == 1

    sent_email = mail.outbox[0]
    assert sent_email.subject == "[Anki Generator] Redefina sua senha"
    assert sent_email.to == ["branded-reset@example.com"]

    reset_url_match = RESET_URL_PATTERN.search(sent_email.body)
    assert reset_url_match is not None
    reset_url = reset_url_match.group(0)

    assert "Seu próximo estudo está esperando." in sent_email.body
    assert "Se você não fez esta solicitação" in sent_email.body
    assert "Anki Generator" in sent_email.body

    assert len(sent_email.alternatives) == 1
    html_alternative = sent_email.alternatives[0]
    assert html_alternative.mimetype == "text/html"

    html_body = html_alternative.content
    assert 'lang="pt-BR"' in html_body
    assert "Seu próximo estudo está esperando." in html_body
    assert "Redefinir minha senha" in html_body
    assert f'href="{escape(reset_url, quote=True)}"' in html_body
    assert escape(reset_url) in html_body
    assert "#ff9800" in html_body
    assert "#000000" in html_body
    assert "<img" not in html_body
    assert "@import" not in html_body
```

- [ ] **Step 2: Run the test and verify that the packaged allauth email fails the new contract**

Run from `django/`:

```bash
poetry run pytest apps/accounts/tests/test_password_reset_email.py -q
```

Expected: FAIL because the current message has the packaged allauth subject/body and no `text/html` alternative.

- [ ] **Step 3: Register the project template directory**

Change the Django template configuration in `django/core/settings/base.py`:

```python
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Overrides package templates (notably allauth transactional e-mails)
        # live here. Project DIRS are searched before APP_DIRS.
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
```

- [ ] **Step 4: Add the custom subject and plain-text templates**

Create `django/templates/account/email/password_reset_key_subject.txt`:

```django
{% autoescape off %}Redefina sua senha{% endautoescape %}
```

Create `django/templates/account/email/password_reset_key_message.txt`:

```django
{% autoescape off %}Seu próximo estudo está esperando.

Recebemos uma solicitação para redefinir a senha da sua conta no Anki Generator.

Redefina sua senha usando este link:
{{ password_reset_url }}

Se você não fez esta solicitação, ignore este e-mail. Sua senha continuará a mesma.

Por segurança, não encaminhe este link para outras pessoas.

Anki Generator
Flashcards inteligentes. Aprendizado que evolui.

Esta é uma mensagem automática. Não é preciso responder.{% endautoescape %}
```

- [ ] **Step 5: Add the approved “Dark premium” HTML template**

Create `django/templates/account/email/password_reset_key_message.html`:

```django
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="color-scheme" content="dark">
    <meta name="supported-color-schemes" content="dark">
    <title>Redefina sua senha</title>
    <style>
      :root { color-scheme: dark; supported-color-schemes: dark; }
      @media only screen and (max-width: 620px) {
        .email-shell { width: 100% !important; }
        .mobile-padding { padding-right: 20px !important; padding-left: 20px !important; }
        .content-card { padding: 30px 22px !important; }
        .email-title { font-size: 29px !important; line-height: 35px !important; }
      }
    </style>
  </head>
  <body style="margin:0; padding:0; background-color:#000000; color:#ffffff;">
    <div style="display:none; max-height:0; overflow:hidden; opacity:0; color:transparent;">
      Use o link seguro para criar uma nova senha no Anki Generator.
    </div>
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" bgcolor="#000000" style="width:100%; background-color:#000000;">
      <tr>
        <td class="mobile-padding" align="center" style="padding:36px 24px 44px;">
          <table role="presentation" class="email-shell" width="600" cellspacing="0" cellpadding="0" border="0" style="width:100%; max-width:600px;">
            <tr>
              <td height="6" bgcolor="#ff9800" style="height:6px; border-radius:999px; background-color:#ff9800; font-size:0; line-height:0;">&nbsp;</td>
            </tr>
            <tr>
              <td style="padding:24px 8px 28px;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                  <tr>
                    <td width="38" height="38" align="center" valign="middle" bgcolor="#ff9800" style="width:38px; height:38px; border-radius:10px; background-color:#ff9800; color:#000000; font-family:Arial,Helvetica,sans-serif; font-size:13px; font-weight:800;">AG</td>
                    <td style="padding-left:12px; color:#ffffff; font-family:Arial,Helvetica,sans-serif; font-size:20px; font-weight:800; letter-spacing:-0.4px;">Anki <span style="color:#ff9800;">Generator</span></td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td class="content-card" bgcolor="#161616" style="padding:42px 40px; border:1px solid #333333; border-radius:18px; background-color:#161616;">
                <p style="margin:0 0 13px; color:#ff9800; font-family:Arial,Helvetica,sans-serif; font-size:11px; font-weight:800; line-height:16px; letter-spacing:1.7px; text-transform:uppercase;">Recuperação de acesso</p>
                <h1 class="email-title" style="margin:0 0 18px; color:#ffffff; font-family:Arial,Helvetica,sans-serif; font-size:36px; font-weight:800; line-height:42px; letter-spacing:-1px;">Seu próximo estudo está esperando.</h1>
                <p style="margin:0 0 28px; color:#c7c7c7; font-family:Arial,Helvetica,sans-serif; font-size:16px; line-height:25px;">Recebemos uma solicitação para redefinir a senha da sua conta. Use o botão abaixo para criar uma nova senha.</p>
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin:0 0 30px;">
                  <tr>
                    <td align="center" bgcolor="#ff9800" style="border-radius:999px; background-color:#ff9800; mso-padding-alt:15px 26px;">
                      <a href="{{ password_reset_url }}" style="display:inline-block; padding:15px 26px; color:#000000; font-family:Arial,Helvetica,sans-serif; font-size:15px; font-weight:800; line-height:20px; text-decoration:none;">Redefinir minha senha &rarr;</a>
                    </td>
                  </tr>
                </table>
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" bgcolor="#222222" style="width:100%; background-color:#222222; border-radius:12px;">
                  <tr>
                    <td style="padding:17px 18px; color:#aaaaaa; font-family:Arial,Helvetica,sans-serif; font-size:13px; line-height:20px;">
                      <strong style="color:#ffffff;">Sua conta continua protegida.</strong><br>
                      Se você não fez esta solicitação, ignore este e-mail. Sua senha continuará a mesma.
                    </td>
                  </tr>
                </table>
                <p style="margin:26px 0 7px; color:#8e8e8e; font-family:Arial,Helvetica,sans-serif; font-size:12px; line-height:18px;">Se o botão não funcionar, copie e cole este endereço no navegador:</p>
                <p style="margin:0; color:#ff9800; font-family:Arial,Helvetica,sans-serif; font-size:12px; line-height:18px; word-break:break-all;"><a href="{{ password_reset_url }}" style="color:#ff9800; text-decoration:underline;">{{ password_reset_url }}</a></p>
              </td>
            </tr>
            <tr>
              <td style="padding:25px 8px 0; color:#858585; font-family:Arial,Helvetica,sans-serif; font-size:12px; line-height:19px;">
                <strong style="color:#bdbdbd;">Anki Generator</strong><br>
                Flashcards inteligentes. Aprendizado que evolui.<br><br>
                Esta é uma mensagem automática. Não é preciso responder.
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
```

- [ ] **Step 6: Run the focused test and confirm the multipart contract passes**

Run from `django/`:

```bash
poetry run pytest apps/accounts/tests/test_password_reset_email.py -q
```

Expected: `1 passed`.

- [ ] **Step 7: Commit the focused implementation without staging unrelated Sprint 9 work**

```bash
git add django/templates/account/email/password_reset_key_subject.txt \
  django/templates/account/email/password_reset_key_message.txt \
  django/templates/account/email/password_reset_key_message.html \
  django/apps/accounts/tests/test_password_reset_email.py
git add -p django/core/settings/base.py
git diff --cached --check
git diff --cached --stat
git commit -m "feat: brand password reset email"
```

Expected: the staged diff contains only the template-directory setting, the three templates, and the focused email test. If `git add -p` shows a mixed hunk, do not stage it until the feature hunk is isolated.

---

### Task 2: Align Sprint 9 documentation and run regression verification

**Files:**
- Modify: `django/apps/accounts/serializers.py:1-6`
- Modify: `django/apps/accounts/tests/test_password_reset.py:1-6`
- Modify: `openspec/changes/sprint-9-tela-de-estudo/proposal.md`
- Modify: `openspec/changes/sprint-9-tela-de-estudo/tasks.md`
- Modify: `PRD.md:382`
- Modify: `PROMPT_REFINADO.md:516-525`
- Modify: `CHANGELOG.md:15-19`

**Interfaces:**
- Consumes: the verified multipart behavior from Task 1.
- Produces: a consistent Sprint 9 record in which no active document claims that the password-reset email still uses the packaged allauth template.

- [ ] **Step 1: Correct the serializer and test module documentation**

Replace the opening paragraph of `django/apps/accounts/serializers.py` with:

```python
"""
Serializer de recuperação de senha (PRD.md §7.1) — personaliza o link do
e-mail enviado pelo dj-rest-auth para apontar para o frontend (SPA). O assunto
e os corpos texto/HTML são overrides nativos do allauth em
`django/templates/account/email/password_reset_key_*`; continuam separados do
serializer para preservar a responsabilidade de cada camada.
```

Keep the remainder of that module docstring, beginning with `Como o django-allauth está instalado`, and its implementation unchanged.

Replace the opening paragraph of `django/apps/accounts/tests/test_password_reset.py` with:

```python
"""
Recuperação de senha (PRD.md §7.1) — link apontando para o frontend e
confirmação via o token assinado do allauth (`EmailAwarePasswordResetTokenGenerator`,
subclasse do `PasswordResetTokenGenerator` do próprio Django), sem uma view
HTML server-rendered no backend API-only. A renderização multipart do e-mail é
coberta separadamente por `test_password_reset_email.py`.
```

Keep the rest of the module docstring and all existing behavioral tests unchanged.

- [ ] **Step 2: Update the Sprint 9 OpenSpec records**

Add this bullet to `openspec/changes/sprint-9-tela-de-estudo/proposal.md` under `## What Changes`:

```markdown
- E-mail de recuperação do allauth customizado em texto + HTML com a identidade “Dark premium” do Anki Generator; token, URL da SPA e transporte Resend permanecem inalterados.
```

Add this capability to `## Capabilities` → `### New Capabilities`:

```markdown
- `branded-password-reset-email`: override nativo dos templates de recuperação do allauth, com assunto, fallback textual e HTML responsivo próprios.
```

Add this impact item under `## Impact`:

```markdown
- Backend de autenticação: diretório de templates do projeto, três templates `account/email/password_reset_key_*` e teste de renderização multipart; nenhum impacto no React.
```

Append this section to `openspec/changes/sprint-9-tela-de-estudo/tasks.md`:

```markdown
## 6. E-mail customizado de recuperação de senha

- [x] 6.1 Sobrescrever assunto e corpos texto/HTML de `account/email/password_reset_key` com a identidade “Dark premium” do Anki Generator
- [x] 6.2 Manter `password_reset_url`, token assinado, proteção contra enumeração e telas React sem alterações comportamentais
- [x] 6.3 Testar mensagem multipart, assunto, CTA, fallback de URL e ausência de recursos externos
```

- [ ] **Step 3: Replace the superseded product decision in canonical docs**

In `PRD.md` §7.1, replace the sentence saying the template remains the allauth default with:

```markdown
O e-mail usa templates próprios em texto + HTML, com a identidade visual “Dark premium” do Anki Generator e sem recursos externos; token, link da SPA e telas React permanecem inalterados.
```

In `<decisao_resolvida id="recuperacao-de-senha-resend">` in `PROMPT_REFINADO.md`, replace the explicit decision to keep the default template with:

```markdown
**Decisão revisada na Sprint 9**: o e-mail passa a sobrescrever nativamente `account/email/password_reset_key` em assunto, texto puro e HTML “Dark premium”. O diretório de templates do projeto tem precedência sobre `APP_DIRS`; não há adapter ou formulário customizado, recursos externos, alteração de token, URL da SPA ou telas React.
```

In the Sprint 9 entry of `CHANGELOG.md`, replace the statement that the allauth template remains standard with:

```markdown
- `templates/account/email/password_reset_key_*`: assunto e corpos texto/HTML próprios com identidade “Dark premium” do Anki Generator, CTA e URL alternativa; sem imagens, fontes ou tracking externos. O allauth continua responsável pela mensagem multipart, token e envio.
```

- [ ] **Step 4: Verify that no stale active decision remains**

Run from the repository root:

```bash
rg -n "template do e-mail continua o padrão|template padrão do allauth|não reescrevê-lo" \
  PRD.md PROMPT_REFINADO.md CHANGELOG.md \
  django/apps/accounts/serializers.py \
  django/apps/accounts/tests/test_password_reset.py \
  openspec/changes/sprint-9-tela-de-estudo
```

Expected: no matches.

- [ ] **Step 5: Run password-reset regression tests**

Run from `django/`:

```bash
poetry run pytest \
  apps/accounts/tests/test_password_reset.py \
  apps/accounts/tests/test_password_reset_email.py \
  -q
```

Expected: `6 passed`.

- [ ] **Step 6: Run formatting and Django configuration checks**

Run from `django/`:

```bash
poetry run black --check apps/accounts/tests/test_password_reset_email.py
poetry run python manage.py check
```

Expected: Black reports the file unchanged and Django reports `System check identified no issues`.

- [ ] **Step 7: Inspect the final scope**

Run from the repository root:

```bash
git diff --check
git status --short
git diff -- frontend
```

Expected: no whitespace errors, all created/modified email files are visible in status, and `git diff -- frontend` contains no changes caused by this feature.

- [ ] **Step 8: Commit only documentation hunks owned by this change**

Because the Sprint 9 documents already contain unrelated uncommitted work, stage only the new email-documentation hunks:

```bash
git add -p django/apps/accounts/serializers.py \
  django/apps/accounts/tests/test_password_reset.py \
  openspec/changes/sprint-9-tela-de-estudo/proposal.md \
  openspec/changes/sprint-9-tela-de-estudo/tasks.md \
  PRD.md PROMPT_REFINADO.md CHANGELOG.md
git diff --cached --check
git diff --cached --stat
git commit -m "docs: record branded reset email"
```

Expected: only the documentation changes described in this task are staged; all pre-existing user changes remain unstaged.
