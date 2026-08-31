"""
Ciclo de vida de soft delete — Deck/Card/Category (Sprint 6,
`soft-delete-lifecycle`, `deck-daily-review-goal`, `deck-card-full-edit`).
Ver openspec/changes/sprint-6-ciclo-de-vida-deck-card/specs/.
"""

from datetime import datetime, timedelta, timezone

import pytest
from django.core.cache import cache

from apps.decks.infrastructure.repositories.card_repository import CardRepository
from apps.decks.infrastructure.repositories.card_review_repository import CardReviewRepository
from apps.decks.infrastructure.repositories.category_repository import CategoryRepository
from apps.decks.infrastructure.repositories.deck_repository import DeckRepository
from apps.decks.tasks import RETENTION_DAYS, purge_soft_deleted

from .conftest import backdate_deleted_at, read_raw_document, run_async


def _create_card(client, deck_id, **overrides):
    payload = {
        "front": "network",
        "back": "rede",
        "front_description": "The network is down today.",
        "back_description": "A rede esta fora do ar hoje.",
        "deck_id": deck_id,
        **overrides,
    }
    return client.post("/api/v1/cards/", payload, format="json")


@pytest.mark.django_db
def test_deck_soft_delete_sets_deleted_at_and_excludes_from_reads(client_a, owner_a):
    response = client_a.post("/api/v1/decks/", {"title": "Deck a excluir"}, format="json")
    deck_id = response.data["id"]

    cache.clear()
    client_a.delete(f"/api/v1/decks/{deck_id}/")

    assert run_async(DeckRepository().find_by_id(deck_id, str(owner_a.id))) is None

    document = read_raw_document("decks", deck_id)
    assert document is not None
    assert document["deleted_at"] is not None


@pytest.mark.django_db
def test_card_soft_delete_sets_deleted_at_and_excludes_from_reads(client_a, owner_a):
    deck_response = client_a.post("/api/v1/decks/", {"title": "Deck"}, format="json")
    deck_id = deck_response.data["id"]

    cache.clear()
    card_response = _create_card(client_a, deck_id)
    card_id = card_response.data["id"]

    cache.clear()
    client_a.delete(f"/api/v1/cards/{card_id}/")

    assert run_async(CardRepository().find_by_id(card_id, str(owner_a.id))) is None

    document = read_raw_document("cards", card_id)
    assert document is not None
    assert document["deleted_at"] is not None


@pytest.mark.django_db
def test_category_soft_delete_sets_deleted_at_and_excludes_from_reads(client_a, owner_a):
    response = client_a.post("/api/v1/categories/", {"name": "Programação"}, format="json")
    category_id = response.data["id"]

    cache.clear()
    client_a.delete(f"/api/v1/categories/{category_id}/")

    assert run_async(CategoryRepository().find_by_id(category_id, str(owner_a.id))) is None

    document = read_raw_document("categories", category_id)
    assert document is not None
    assert document["deleted_at"] is not None


@pytest.mark.django_db
def test_deck_deletion_cascades_soft_delete_to_cards(client_a, owner_a):
    deck_response = client_a.post("/api/v1/decks/", {"title": "Deck com cards"}, format="json")
    deck_id = deck_response.data["id"]

    cache.clear()
    card_response = _create_card(client_a, deck_id)
    card_id = card_response.data["id"]

    cache.clear()
    client_a.delete(f"/api/v1/decks/{deck_id}/")

    assert run_async(CardRepository().find_by_id(card_id, str(owner_a.id))) is None
    document = read_raw_document("cards", card_id)
    assert document["deleted_at"] is not None


@pytest.mark.django_db
def test_category_deletion_unlinks_referencing_decks_without_deleting_them(client_a, owner_a):
    category_response = client_a.post("/api/v1/categories/", {"name": "Trabalho"}, format="json")
    category_id = category_response.data["id"]

    cache.clear()
    deck_response = client_a.post(
        "/api/v1/decks/", {"title": "Deck com categoria", "category_id": category_id}, format="json"
    )
    deck_id = deck_response.data["id"]
    assert deck_response.data["id"] is not None

    cache.clear()
    delete_response = client_a.delete(f"/api/v1/categories/{category_id}/")
    assert delete_response.status_code == 204

    deck = run_async(DeckRepository().find_by_id(deck_id, str(owner_a.id)))
    assert deck is not None
    assert deck.category_id is None


@pytest.mark.django_db
def test_card_review_survives_card_and_deck_deletion(client_a, owner_a):
    deck_response = client_a.post("/api/v1/decks/", {"title": "Deck de revisão"}, format="json")
    deck_id = deck_response.data["id"]

    cache.clear()
    card_response = _create_card(client_a, deck_id)
    card_id = card_response.data["id"]

    cache.clear()
    review_response = client_a.post(f"/api/v1/cards/{card_id}/review/", {"rating": "good"}, format="json")
    assert review_response.status_code == 201

    cache.clear()
    client_a.delete(f"/api/v1/decks/{deck_id}/")

    reviews = run_async(CardReviewRepository().find_by_owner(str(owner_a.id)))
    assert len(reviews) == 1
    assert str(reviews[0].card_id) == card_id


@pytest.mark.django_db
def test_purge_removes_records_older_than_retention_window_and_preserves_recent(client_a, owner_a):
    old_deck_response = client_a.post("/api/v1/decks/", {"title": "Deck antigo"}, format="json")
    old_deck_id = old_deck_response.data["id"]

    cache.clear()
    recent_deck_response = client_a.post("/api/v1/decks/", {"title": "Deck recente"}, format="json")
    recent_deck_id = recent_deck_response.data["id"]

    cache.clear()
    client_a.delete(f"/api/v1/decks/{old_deck_id}/")
    cache.clear()
    client_a.delete(f"/api/v1/decks/{recent_deck_id}/")

    long_ago = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS + 1)
    backdate_deleted_at("decks", old_deck_id, long_ago)

    purge_soft_deleted()

    assert read_raw_document("decks", old_deck_id) is None
    assert read_raw_document("decks", recent_deck_id) is not None


@pytest.mark.django_db
def test_daily_review_goal_editable_via_patch_and_absent_by_default(client_a):
    create_response = client_a.post("/api/v1/decks/", {"title": "Deck com meta"}, format="json")
    assert create_response.data.get("daily_review_goal") is None
    deck_id = create_response.data["id"]

    cache.clear()
    patch_response = client_a.patch(
        f"/api/v1/decks/{deck_id}/", {"daily_review_goal": 20}, format="json"
    )
    assert patch_response.status_code == 200
    assert patch_response.data["daily_review_goal"] == 20


@pytest.mark.django_db
def test_patch_deck_ignores_owner_and_audit_fields_in_payload(client_a, owner_a):
    create_response = client_a.post("/api/v1/decks/", {"title": "Deck protegido"}, format="json")
    deck_id = create_response.data["id"]

    cache.clear()
    client_a.patch(
        f"/api/v1/decks/{deck_id}/",
        {"title": "Deck renomeado", "owner_id": "attacker", "created_by": "attacker", "updated_by": "attacker"},
        format="json",
    )

    deck = run_async(DeckRepository().find_by_id(deck_id, str(owner_a.id)))
    assert deck.owner_id == str(owner_a.id)
    assert deck.created_by == str(owner_a.id)
    assert deck.updated_by == str(owner_a.id)


@pytest.mark.django_db
def test_patch_card_ignores_owner_and_audit_fields_in_payload(client_a, owner_a):
    deck_response = client_a.post("/api/v1/decks/", {"title": "Deck"}, format="json")
    deck_id = deck_response.data["id"]

    cache.clear()
    card_response = _create_card(client_a, deck_id)
    card_id = card_response.data["id"]

    cache.clear()
    client_a.patch(
        f"/api/v1/cards/{card_id}/",
        {"context": "infra", "owner_id": "attacker", "created_by": "attacker", "updated_by": "attacker"},
        format="json",
    )

    card = run_async(CardRepository().find_by_id(card_id, str(owner_a.id)))
    assert card.owner_id == str(owner_a.id)
    assert card.created_by == str(owner_a.id)
    assert card.updated_by == str(owner_a.id)
