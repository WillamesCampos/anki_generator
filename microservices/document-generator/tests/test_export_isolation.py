"""Isolamento de arquivos entre exportações (Sprint 11, D10): duas
requisições — inclusive com decks de mesmo título — nunca leem nem
sobrescrevem os arquivos uma da outra, e nada fica no volume depois."""

import uuid

import pytest

from app.generator import generate_deck_package
from tests.apkg_helpers import read_apkg
from tests.conftest import EXPORT_PAYLOAD, FakeTTS, make_service_token
from tests.test_stable_anki_ids import DECK_A, DECK_B, make_card

EXPORT_PATH = "/document-generator/v1/decks/export"


def auth():
    return {"Authorization": f"Bearer {make_service_token()}"}


def test_same_title_same_day_produces_distinct_files_with_their_own_cards(tmp_path):
    first = generate_deck_package(
        deck_id=str(DECK_A),
        deck_title="Inglês",
        cards=[make_card(uuid.UUID(int=1), front="only in A")],
        output_dir=tmp_path,
    )
    second = generate_deck_package(
        deck_id=str(DECK_B),
        deck_title="Inglês",
        cards=[make_card(uuid.UUID(int=2), front="only in B")],
        output_dir=tmp_path,
    )

    assert first != second
    assert first.exists() and second.exists()
    assert "only in A" in read_apkg(first)["notes"][0]["fields"][0]
    assert "only in B" in read_apkg(second)["notes"][0]["fields"][0]


def test_failed_generation_leaves_no_files_behind(tmp_path, monkeypatch):
    class ExplodingTTS(FakeTTS):
        """Falha só no segundo card — o áudio do primeiro já está no disco."""

        def save(self, path):
            if self.text == "boom":
                raise RuntimeError("gTTS fora do ar")
            super().save(path)

    monkeypatch.setattr("app.generator.gTTS", ExplodingTTS)

    with pytest.raises(RuntimeError):
        generate_deck_package(
            deck_id=str(DECK_A),
            deck_title="Deck",
            cards=[
                make_card(uuid.UUID(int=1), front="hello"),
                make_card(uuid.UUID(int=2), front="boom"),
            ],
            output_dir=tmp_path,
        )

    assert list(tmp_path.rglob("*.mp3")) == []
    assert list(tmp_path.rglob("*.apkg")) == []


def test_working_files_are_removed_after_the_response_is_sent(client, audio_dir):
    response = client.post(EXPORT_PATH, json=EXPORT_PAYLOAD, headers=auth())

    assert response.status_code == 200
    assert response.content[:2] == b"PK"  # o .apkg (zip) chegou inteiro
    assert list(audio_dir.rglob("*.apkg")) == []
    assert list(audio_dir.rglob("*.mp3")) == []
