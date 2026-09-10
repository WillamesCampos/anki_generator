"""
Recuperação de senha (PRD.md §7.1) — link apontando para o frontend e
confirmação via o token assinado do allauth (`EmailAwarePasswordResetTokenGenerator`,
subclasse do `PasswordResetTokenGenerator` do próprio Django), sem uma view
HTML server-rendered no backend API-only. A renderização multipart do e-mail é
coberta separadamente por `test_password_reset_email.py`.

`uid`/`token` seguem a codificação do allauth (base36 pra PK inteira, não o
base64 do Django puro) porque `dj-rest-auth` delega pro
`AllAuthPasswordResetForm` quando `allauth` está em `INSTALLED_APPS` — ver
apps/accounts/serializers.py.
"""

import re

import pytest
from allauth.account.forms import default_token_generator
from allauth.account.utils import user_pk_to_url_str
from django.core import mail
from rest_framework.test import APIClient

from apps.accounts.models import User

RESET_LINK_PATTERN = re.compile(
    r"http://localhost:5173/redefinir-senha\?uid=([\w-]+)&token=([\w.%+-]+)"
)


@pytest.mark.django_db
def test_password_reset_sends_email_with_frontend_link():
    User.objects.create_user(
        username="reset1", email="reset1@example.com", password="senha-antiga-123"
    )

    client = APIClient()
    response = client.post(
        "/api/v1/auth/password/reset/", {"email": "reset1@example.com"}, format="json"
    )

    assert response.status_code == 200
    assert len(mail.outbox) == 1

    sent_email = mail.outbox[0]
    assert sent_email.to == ["reset1@example.com"]

    match = RESET_LINK_PATTERN.search(sent_email.body)
    assert (
        match is not None
    ), "corpo do e-mail deveria conter o link do frontend com uid/token"


@pytest.mark.django_db
def test_password_reset_unknown_email_does_not_leak_existence():
    """Mesma resposta (200, sem e-mail enviado) pra e-mail que não existe —
    não revela se a conta existe, mesmo princípio já usado no 404 de
    recursos de outro dono (ver apps/decks)."""
    client = APIClient()
    response = client.post(
        "/api/v1/auth/password/reset/",
        {"email": "nao-existe@example.com"},
        format="json",
    )

    assert response.status_code == 200
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_password_reset_confirm_changes_password_and_allows_login():
    User.objects.create_user(
        username="reset2", email="reset2@example.com", password="senha-antiga-123"
    )

    client = APIClient()
    client.post(
        "/api/v1/auth/password/reset/", {"email": "reset2@example.com"}, format="json"
    )

    match = RESET_LINK_PATTERN.search(mail.outbox[0].body)
    uid, token = match.group(1), match.group(2)

    confirm_response = client.post(
        "/api/v1/auth/password/reset/confirm/",
        {
            "uid": uid,
            "token": token,
            "new_password1": "senha-nova-456",
            "new_password2": "senha-nova-456",
        },
        format="json",
    )
    assert confirm_response.status_code == 200

    login_response = client.post(
        "/api/v1/auth/login/",
        {"email": "reset2@example.com", "password": "senha-nova-456"},
        format="json",
    )
    assert login_response.status_code == 200

    old_password_login = client.post(
        "/api/v1/auth/login/",
        {"email": "reset2@example.com", "password": "senha-antiga-123"},
        format="json",
    )
    assert old_password_login.status_code == 400


@pytest.mark.django_db
def test_password_reset_confirm_rejects_reused_token():
    """O token é invalidado depois do primeiro uso — a senha muda, e o
    token é derivado (entre outras coisas) do hash da senha atual."""
    user = User.objects.create_user(
        username="reset3", email="reset3@example.com", password="senha-antiga-123"
    )
    uid = user_pk_to_url_str(user)
    token = default_token_generator.make_token(user)

    client = APIClient()
    first_attempt = client.post(
        "/api/v1/auth/password/reset/confirm/",
        {
            "uid": uid,
            "token": token,
            "new_password1": "senha-nova-456",
            "new_password2": "senha-nova-456",
        },
        format="json",
    )
    assert first_attempt.status_code == 200

    second_attempt = client.post(
        "/api/v1/auth/password/reset/confirm/",
        {
            "uid": uid,
            "token": token,
            "new_password1": "outra-senha-789",
            "new_password2": "outra-senha-789",
        },
        format="json",
    )
    assert second_attempt.status_code == 400


@pytest.mark.django_db
def test_password_reset_confirm_rejects_invalid_token():
    user = User.objects.create_user(
        username="reset4", email="reset4@example.com", password="senha-antiga-123"
    )
    uid = user_pk_to_url_str(user)

    client = APIClient()
    response = client.post(
        "/api/v1/auth/password/reset/confirm/",
        {
            "uid": uid,
            "token": "token-adulterado-invalido",
            "new_password1": "senha-nova-456",
            "new_password2": "senha-nova-456",
        },
        format="json",
    )
    assert response.status_code == 400
