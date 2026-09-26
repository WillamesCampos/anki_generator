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


class FakeTTS:
    """Substitui o gTTS (chamada de rede ao Google) nos testes — grava um
    arquivo pequeno e registra cada texto pedido em `FakeTTS.calls`."""

    calls: list[str] = []

    def __init__(self, text, lang="en", tld="com", **kwargs):
        self.text = text
        FakeTTS.calls.append(text)

    def save(self, path):
        with open(path, "wb") as f:
            f.write(b"ID3-fake-audio:" + self.text.encode())


@pytest.fixture(autouse=True)
def tts_calls(monkeypatch):
    """Nenhum teste chama o gTTS de verdade; devolve a lista de textos pedidos."""
    FakeTTS.calls = []
    monkeypatch.setattr("app.generator.gTTS", FakeTTS)
    return FakeTTS.calls


@pytest.fixture(autouse=True)
def audio_dir(monkeypatch, tmp_path):
    """Diretório de saída isolado por teste (o padrão `/data/anki_audio` só
    existe dentro do container)."""
    path = tmp_path / "anki_audio"
    monkeypatch.setenv("AUDIO_OUTPUT_DIR", str(path))
    get_settings.cache_clear()
    return path


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
    "deck_id": "0b0f0b1e-6f6d-4d8e-9c47-2f1f5f0a1111",
    "deck_title": "Deck de teste",
    "cards": [
        {
            "id": "c1a1c1a1-0000-4000-8000-000000000001",
            "front": "hello",
            "back": "olá",
            "front_description": "Hello, how are you?",
            "back_description": "Olá, como vai você?",
        }
    ],
}
