"""
Cobre a blocklist de refresh token (D1 em design.md desta sprint). O
handshake real com o Google (django-allauth) não é testado aqui — é
integração com um provedor externo, fora do escopo de teste automatizado;
o que importa testar é a emissão/revogação de JWT, que já assume um usuário
autenticado.
"""

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.accounts.tokens import is_refresh_token_revoked


@pytest.mark.django_db
def test_refresh_token_works_before_revocation():
    user = User.objects.create_user(username="auth1", email="auth1@example.com")
    refresh = RefreshToken.for_user(user)

    client = APIClient()
    response = client.post("/api/v1/auth/token/refresh/", {"refresh": str(refresh)}, format="json")

    assert response.status_code == 200
    assert "access" in response.data


@pytest.mark.django_db
def test_logout_revokes_refresh_token_and_blocks_future_refresh():
    user = User.objects.create_user(username="auth2", email="auth2@example.com")
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    logout_response = client.post("/api/v1/auth/logout/", {"refresh": str(refresh)}, format="json")
    assert logout_response.status_code == 200
    assert is_refresh_token_revoked(refresh["jti"]) is True

    client.credentials()  # remove o header de auth pra chamada seguinte
    refresh_response = client.post(
        "/api/v1/auth/token/refresh/", {"refresh": str(refresh)}, format="json"
    )
    assert refresh_response.status_code == 401
