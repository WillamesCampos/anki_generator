"""
Fixtures dos testes do `document-generator` (Sprint 5, JWT de serviço).

`get_settings()` é `@lru_cache` (`app/config.py`) — sem limpar o cache entre
testes, o primeiro valor de `SERVICE_JWT_KEYS` lido "gruda" nos testes
seguintes mesmo mudando a env var. `_clear_settings_cache` garante que cada
teste enxerga o `.env`/env var atual.
"""

import time

import jwt
import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app

SIGNING_SECRET = "test-signing-secret"
SIGNING_KID = "v1"
AUDIENCE = "document-generator"


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def configured_keys(monkeypatch):
    """`document-generator` configurado pra aceitar `SIGNING_KID`/`SIGNING_SECRET`."""
    monkeypatch.setenv("SERVICE_JWT_KEYS", f'{{"{SIGNING_KID}": "{SIGNING_SECRET}"}}')
    get_settings.cache_clear()


@pytest.fixture
def client(configured_keys) -> TestClient:
    return TestClient(app)


def make_service_token(
    *,
    secret: str = SIGNING_SECRET,
    kid: str = SIGNING_KID,
    audience: str = AUDIENCE,
    issuer: str = "django-core",
    expires_in: int = 60,
) -> str:
    now = int(time.time())
    payload = {
        "iss": issuer,
        "aud": audience,
        "iat": now,
        "exp": now + expires_in,
        "jti": "test-jti",
    }
    return jwt.encode(payload, secret, algorithm="HS256", headers={"kid": kid})


EXPORT_PAYLOAD = {
    "deck_title": "Deck de teste",
    "cards": [
        {
            "front": "hello",
            "back": "olá",
            "front_description": "Hello, how are you?",
            "back_description": "Olá, como vai você?",
        }
    ],
}
