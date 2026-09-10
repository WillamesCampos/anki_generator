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
    assert "Por segurança, não encaminhe este link para outras pessoas." in html_body
    assert "Redefinir minha senha" in html_body
    assert f'href="{escape(reset_url, quote=True)}"' in html_body
    assert escape(reset_url) in html_body
    assert "#ff9800" in html_body
    assert "#000000" in html_body
    assert "<img" not in html_body
    assert "@import" not in html_body
