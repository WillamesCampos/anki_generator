"""
`created_by`/`updated_by` em Deck/Card/Category/CardReview (Sprint 5,
`auditoria-entidades-mongo`) — preenchidos pelos serializers a partir da
request autenticada, nunca aceitos como input do cliente. Ver
openspec/changes/sprint-5-fundacoes-transversais/specs/mongo-entity-audit-trail/spec.md.
"""

import pytest

from apps.decks.infrastructure.repositories.card_repository import CardRepository
from apps.decks.infrastructure.repositories.category_repository import (
    CategoryRepository,
)
from apps.decks.infrastructure.repositories.deck_repository import DeckRepository


@pytest.mark.django_db
def test_deck_create_sets_created_by_and_updated_by(client_a, owner_a):
    response = client_a.post(
        "/api/v1/decks/", {"title": "Deck Auditado"}, format="json"
    )
    deck_id = response.data["id"]

    deck = DeckRepository().find_by_id(deck_id, str(owner_a.id))

    assert deck.created_by == str(owner_a.id)
    assert deck.updated_by == str(owner_a.id)


@pytest.mark.django_db
def test_deck_create_ignores_client_supplied_audit_fields(client_a, owner_a):
    response = client_a.post(
        "/api/v1/decks/",
        {"title": "Deck Spoof", "created_by": "attacker", "updated_by": "attacker"},
        format="json",
    )
    deck_id = response.data["id"]

    deck = DeckRepository().find_by_id(deck_id, str(owner_a.id))

    assert deck.created_by == str(owner_a.id)
    assert deck.created_by != "attacker"


@pytest.mark.django_db
def test_deck_update_refreshes_updated_by_keeps_created_by(client_a, owner_a):
    create_response = client_a.post(
        "/api/v1/decks/", {"title": "Original"}, format="json"
    )
    deck_id = create_response.data["id"]

    client_a.patch(f"/api/v1/decks/{deck_id}/", {"title": "Renomeado"}, format="json")

    deck = DeckRepository().find_by_id(deck_id, str(owner_a.id))

    assert deck.created_by == str(owner_a.id)
    assert deck.updated_by == str(owner_a.id)


@pytest.mark.django_db
def test_category_create_sets_created_by(client_a, owner_a):
    response = client_a.post(
        "/api/v1/categories/", {"name": "Programação"}, format="json"
    )
    category_id = response.data["id"]

    category = CategoryRepository().find_by_id(category_id, str(owner_a.id))

    assert category.created_by == str(owner_a.id)
    assert category.updated_by == str(owner_a.id)


@pytest.mark.django_db
def test_card_create_sets_created_by(client_a, owner_a):
    deck_response = client_a.post(
        "/api/v1/decks/", {"title": "Deck de Cards"}, format="json"
    )
    deck_id = deck_response.data["id"]

    card_response = client_a.post(
        "/api/v1/cards/",
        {
            "front": "network",
            "back": "rede",
            "front_description": "The network is down today.",
            "back_description": "A rede esta fora do ar hoje.",
            "deck_id": deck_id,
        },
        format="json",
    )
    card_id = card_response.data["id"]

    card = CardRepository().find_by_id(card_id, str(owner_a.id))

    assert card.created_by == str(owner_a.id)
    assert card.updated_by == str(owner_a.id)


@pytest.mark.django_db
def test_card_update_refreshes_updated_by(client_a, owner_a):
    deck_response = client_a.post(
        "/api/v1/decks/", {"title": "Deck de Cards"}, format="json"
    )
    deck_id = deck_response.data["id"]

    card_response = client_a.post(
        "/api/v1/cards/",
        {
            "front": "network",
            "back": "rede",
            "front_description": "The network is down today.",
            "back_description": "A rede esta fora do ar hoje.",
            "deck_id": deck_id,
        },
        format="json",
    )
    card_id = card_response.data["id"]

    client_a.patch(f"/api/v1/cards/{card_id}/", {"context": "infra"}, format="json")

    card = CardRepository().find_by_id(card_id, str(owner_a.id))

    assert card.created_by == str(owner_a.id)
    assert card.updated_by == str(owner_a.id)


@pytest.mark.django_db
def test_card_review_sets_created_by_and_updated_by(client_a, owner_a):
    deck_response = client_a.post(
        "/api/v1/decks/", {"title": "Deck de Revisão"}, format="json"
    )
    deck_id = deck_response.data["id"]

    card_response = client_a.post(
        "/api/v1/cards/",
        {
            "front": "network",
            "back": "rede",
            "front_description": "The network is down today.",
            "back_description": "A rede esta fora do ar hoje.",
            "deck_id": deck_id,
        },
        format="json",
    )
    card_id = card_response.data["id"]

    review_response = client_a.post(
        f"/api/v1/cards/{card_id}/review/", {"rating": "good"}, format="json"
    )

    assert review_response.data["created_by"] == str(owner_a.id)
    assert review_response.data["updated_by"] == str(owner_a.id)
