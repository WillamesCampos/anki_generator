"""Contrato mínimo de contagem de cards por deck (Sprint 7)."""

import pytest
from django.core.cache import cache


def card_payload(deck_id, front="network"):
    return {
        "front": front,
        "back": "rede",
        "front_description": "The network is stable today.",
        "back_description": "A rede está estável hoje.",
        "deck_id": deck_id,
    }


@pytest.mark.django_db
def test_card_count_returns_only_count_without_materializing_cards(client_a):
    deck = client_a.post("/api/v1/decks/", {"title": "Deck"}, format="json").data
    cache.clear()
    response = client_a.post("/api/v1/cards/", card_payload(deck["id"]), format="json")
    assert response.status_code == 201

    cache.clear()
    response = client_a.get(f"/api/v1/cards/count/?deck_id={deck['id']}")

    assert response.status_code == 200
    assert response.data == {"count": 1}


@pytest.mark.django_db
def test_card_count_excludes_soft_deleted_cards(client_a):
    deck = client_a.post("/api/v1/decks/", {"title": "Deck"}, format="json").data
    cache.clear()
    card = client_a.post("/api/v1/cards/", card_payload(deck["id"]), format="json").data
    cache.clear()
    client_a.delete(f"/api/v1/cards/{card['id']}/")

    cache.clear()
    response = client_a.get(f"/api/v1/cards/count/?deck_id={deck['id']}")

    assert response.status_code == 200
    assert response.data == {"count": 0}


@pytest.mark.django_db
def test_card_count_does_not_expose_another_owners_cards(client_a, client_b):
    deck = client_a.post("/api/v1/decks/", {"title": "Privado"}, format="json").data
    cache.clear()
    client_a.post("/api/v1/cards/", card_payload(deck["id"]), format="json")

    cache.clear()
    response = client_b.get(f"/api/v1/cards/count/?deck_id={deck['id']}")

    assert response.status_code == 200
    assert response.data == {"count": 0}


@pytest.mark.django_db
@pytest.mark.parametrize("query", ["", "?deck_id=not-a-uuid"])
def test_card_count_requires_a_valid_deck_id(client_a, query):
    response = client_a.get(f"/api/v1/cards/count/{query}")

    assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize(
    "superseded_payload",
    [
        {
            "word": "network",
            "translation": "rede",
            "example_original": "The network is stable today.",
            "example_translated": "A rede está estável hoje.",
        },
        {
            "frente": "network",
            "verso": "rede",
            "descricao_frente": "The network is stable today.",
            "descricao_verso": "A rede está estável hoje.",
        },
    ],
)
def test_card_contract_rejects_superseded_field_names(client_a, superseded_payload):
    deck = client_a.post("/api/v1/decks/", {"title": "Deck"}, format="json").data
    cache.clear()

    response = client_a.post(
        "/api/v1/cards/",
        {
            **superseded_payload,
            "deck_id": deck["id"],
        },
        format="json",
    )

    assert response.status_code == 400
    assert set(response.data) >= {
        "front",
        "back",
        "front_description",
        "back_description",
    }
