"""Teto de 100 cards por exportação (Sprint 11, D9): defesa em profundidade
no `document-generator`, independente da validação feita pelo Django."""

import uuid

from tests.conftest import EXPORT_PAYLOAD, make_service_token

EXPORT_PATH = "/document-generator/v1/decks/export"


def payload_with(n_cards: int) -> dict:
    return {
        **EXPORT_PAYLOAD,
        "cards": [
            {
                "id": str(uuid.UUID(int=i + 1)),
                "front": f"card number {i}",
                "back": "verso",
                "front_description": "Descrição da frente",
                "back_description": "Descrição do verso",
            }
            for i in range(n_cards)
        ],
    }


def post(client, payload):
    token = make_service_token()
    return client.post(EXPORT_PATH, json=payload, headers={"Authorization": f"Bearer {token}"})


def test_export_with_exactly_100_cards_is_accepted(client):
    assert post(client, payload_with(100)).status_code == 200


def test_export_with_more_than_100_cards_is_rejected_without_generating(client, tts_calls):
    response = post(client, payload_with(101))

    assert response.status_code == 400
    assert "100" in response.json()["error"]
    assert tts_calls == []


def test_export_without_cards_is_rejected(client):
    assert post(client, payload_with(0)).status_code == 400
