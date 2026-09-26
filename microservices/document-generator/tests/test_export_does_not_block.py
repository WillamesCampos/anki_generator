"""A geração (gTTS + genanki, síncrona e presa em rede) não pode travar o
event loop (Sprint 11, D10): enquanto um export roda, o health check e as
demais rotas continuam respondendo."""

import asyncio
import time

import httpx
import pytest

from app.main import app
from tests.conftest import EXPORT_PAYLOAD, FakeTTS, make_service_token

EXPORT_PATH = "/document-generator/v1/decks/export"
HEALTH_PATH = "/document-generator/v1/health/"
TTS_DELAY_SECONDS = 1.0


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_health_check_answers_while_an_export_is_generating(
    configured_keys, monkeypatch
):
    class SlowTTS(FakeTTS):
        def save(self, path):
            time.sleep(TTS_DELAY_SECONDS)  # bloqueante, como a rede do gTTS
            super().save(path)

    monkeypatch.setattr("app.generator.gTTS", SlowTTS)
    headers = {"Authorization": f"Bearer {make_service_token()}"}

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        started = time.perf_counter()
        export = asyncio.create_task(
            client.post(EXPORT_PATH, json=EXPORT_PAYLOAD, headers=headers)
        )
        await asyncio.sleep(0.1)  # deixa o export começar a gerar
        health = await client.get(HEALTH_PATH)
        health_done_after = time.perf_counter() - started

        exported = await export

    assert health.status_code == 200
    assert exported.status_code == 200
    # se o export bloqueasse o loop, o health só responderia depois de ~1 s
    assert health_done_after < TTS_DELAY_SECONDS / 2
