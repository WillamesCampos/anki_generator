"""
CRUD dos endpoints de Deck/Category/Card (PRD Sprint 2, 2.1) via Generic
Views do DRF sobre repositório Motor (D2/D3 em
openspec/changes/sprint-2-decks-cards/design.md).

Fluxos com mais de 3 requisições limpam o cache manualmente entre passos —
o throttle de 3 req/s (Sprint 1) é por segundo, não por teste, e uma
sequência de create/get/patch/delete real facilmente excede isso.
"""

import pytest
from django.core.cache import cache


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
    response = client_a.post("/api/v1/decks/", {"title": "Deck Original"}, format="json")
    deck_id = response.data["id"]

    cache.clear()
    response = client_a.patch(f"/api/v1/decks/{deck_id}/", {"title": "Deck Renomeado"}, format="json")
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
    response = client_a.post("/api/v1/categories/", {"name": "Programação"}, format="json")
    assert response.status_code == 201
    category_id = response.data["id"]

    cache.clear()
    response = client_a.delete(f"/api/v1/categories/{category_id}/")
    assert response.status_code == 204


@pytest.mark.django_db
def test_card_create_and_update(client_a):
    response = client_a.post("/api/v1/decks/", {"title": "Deck de Cards"}, format="json")
    deck_id = response.data["id"]

    cache.clear()
    response = client_a.post("/api/v1/cards/", {
        "word": "server",
        "translation": "servidor",
        "example_original": "The server crashed twice today.",
        "example_translated": "O servidor caiu duas vezes hoje.",
        "deck_id": deck_id,
    }, format="json")
    assert response.status_code == 201
    assert response.data["word"] == "server"
    card_id = response.data["id"]

    cache.clear()
    response = client_a.patch(f"/api/v1/cards/{card_id}/", {"context": "infra"}, format="json")
    assert response.status_code == 200
    assert response.data["context"] == "infra"


@pytest.mark.django_db
def test_card_list_filtered_by_deck(client_a):
    response = client_a.post("/api/v1/decks/", {"title": "Deck Filtro"}, format="json")
    deck_id = response.data["id"]

    cache.clear()
    client_a.post("/api/v1/cards/", {
        "word": "database",
        "translation": "banco de dados",
        "example_original": "The database needs a backup soon.",
        "example_translated": "O banco de dados precisa de um backup em breve.",
        "deck_id": deck_id,
    }, format="json")

    cache.clear()
    response = client_a.get(f"/api/v1/cards/?deck_id={deck_id}")
    assert response.status_code == 200
    assert response.data["count"] == 1


@pytest.mark.django_db
def test_cross_tenant_deck_access_returns_404(client_a, client_b):
    response = client_a.post("/api/v1/decks/", {"title": "Privado"}, format="json")
    deck_id = response.data["id"]

    cache.clear()
    response = client_b.get(f"/api/v1/decks/{deck_id}/")
    assert response.status_code == 404
