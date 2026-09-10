"""
CRUD dos endpoints de Deck/Category/Card (PRD Sprint 2, 2.1) via Generic
Views do DRF sobre repositório Motor (D2/D3 em
openspec/changes/sprint-2-decks-cards/design.md).

Fluxos longos limpam o cache manualmente entre passos — o throttle de 10
req/s (Sprint 7) é por segundo, não por teste, e uma
sequência de create/get/patch/delete real facilmente excede isso.
"""

import pytest
from django.core.cache import cache

from apps.decks.domain.entities.card import Card
from apps.decks.domain.entities.deck import Deck
from apps.decks.domain.value_objects.translation import Translation
from apps.decks.domain.value_objects.word import Word
from apps.decks.infrastructure.repositories.card_repository import CardRepository
from apps.decks.infrastructure.repositories.deck_repository import DeckRepository


@pytest.mark.django_db
def test_deck_create_and_list(client_a):
    response = client_a.post("/api/v1/decks/", {"title": "Meu Deck"}, format="json")
    assert response.status_code == 201
    assert response.data["title"] == "Meu Deck"
    assert response.data["card_count"] == 0

    response = client_a.get("/api/v1/decks/")
    assert response.status_code == 200
    assert response.data["count"] == 1


@pytest.mark.django_db
def test_deck_update_and_delete(client_a):
    response = client_a.post(
        "/api/v1/decks/", {"title": "Deck Original"}, format="json"
    )
    deck_id = response.data["id"]

    cache.clear()
    response = client_a.patch(
        f"/api/v1/decks/{deck_id}/", {"title": "Deck Renomeado"}, format="json"
    )
    assert response.status_code == 200
    assert response.data["title"] == "Deck Renomeado"

    cache.clear()
    response = client_a.delete(f"/api/v1/decks/{deck_id}/")
    assert response.status_code == 204

    cache.clear()
    response = client_a.get(f"/api/v1/decks/{deck_id}/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_category_create_and_delete(client_a):
    response = client_a.post(
        "/api/v1/categories/", {"name": "Programação"}, format="json"
    )
    assert response.status_code == 201
    category_id = response.data["id"]

    cache.clear()
    response = client_a.delete(f"/api/v1/categories/{category_id}/")
    assert response.status_code == 204


@pytest.mark.django_db
def test_card_create_and_update(client_a):
    response = client_a.post(
        "/api/v1/decks/", {"title": "Deck de Cards"}, format="json"
    )
    deck_id = response.data["id"]

    cache.clear()
    response = client_a.post(
        "/api/v1/cards/",
        {
            "front": "server",
            "back": "servidor",
            "front_description": "The server crashed twice today.",
            "back_description": "O servidor caiu duas vezes hoje.",
            "deck_id": deck_id,
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["front"] == "server"
    card_id = response.data["id"]

    cache.clear()
    response = client_a.patch(
        f"/api/v1/cards/{card_id}/", {"context": "infra"}, format="json"
    )
    assert response.status_code == 200
    assert response.data["context"] == "infra"


@pytest.mark.django_db
def test_card_list_filtered_by_deck(client_a):
    response = client_a.post("/api/v1/decks/", {"title": "Deck Filtro"}, format="json")
    deck_id = response.data["id"]

    cache.clear()
    client_a.post(
        "/api/v1/cards/",
        {
            "front": "database",
            "back": "banco de dados",
            "front_description": "The database needs a backup soon.",
            "back_description": "O banco de dados precisa de um backup em breve.",
            "deck_id": deck_id,
        },
        format="json",
    )

    cache.clear()
    response = client_a.get(f"/api/v1/cards/?deck_id={deck_id}")
    assert response.status_code == 200
    assert response.data["count"] == 1


@pytest.mark.django_db
def test_card_list_is_paginated_ten_at_a_time(client_a, owner_a):
    owner_id = str(owner_a.id)
    deck = DeckRepository().save(Deck(title="Deck paginado", owner_id=owner_id))

    fronts = [
        "alpha",
        "bravo",
        "charlie",
        "delta",
        "echo",
        "foxtrot",
        "golf",
        "hotel",
        "india",
        "juliet",
        "kilo",
    ]

    for front in fronts:
        CardRepository().save(
            Card(
                front=Word(front),
                back=Translation(f"tradução de {front}"),
                front_description=f"Description for {front} card.",
                back_description=f"Descrição suficientemente longa de {front}.",
                owner_id=owner_id,
                deck_id=deck.id,
            )
        )

    first_page = client_a.get(f"/api/v1/cards/?deck_id={deck.id}&page=1")
    second_page = client_a.get(f"/api/v1/cards/?deck_id={deck.id}&page=2")

    assert first_page.status_code == 200
    assert first_page.data["count"] == 11
    assert len(first_page.data["results"]) == 10
    assert first_page.data["next"] is not None
    assert first_page.data["previous"] is None

    assert second_page.status_code == 200
    assert second_page.data["count"] == 11
    assert len(second_page.data["results"]) == 1
    assert second_page.data["next"] is None
    assert second_page.data["previous"] is not None


@pytest.mark.django_db
def test_cross_tenant_deck_access_returns_404(client_a, client_b):
    response = client_a.post("/api/v1/decks/", {"title": "Privado"}, format="json")
    deck_id = response.data["id"]

    cache.clear()
    response = client_b.get(f"/api/v1/decks/{deck_id}/")
    assert response.status_code == 404
