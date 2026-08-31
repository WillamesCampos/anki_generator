from datetime import datetime, timedelta, timezone

import pytest

from apps.decks.domain.entities.card import Card
from apps.decks.domain.entities.card_review import CardReview
from apps.decks.domain.entities.deck import Deck
from apps.decks.domain.value_objects.translation import Translation
from apps.decks.domain.value_objects.word import Word
from apps.decks.infrastructure.repositories.card_repository import CardRepository
from apps.decks.infrastructure.repositories.card_review_repository import CardReviewRepository
from apps.decks.infrastructure.repositories.deck_repository import DeckRepository
from apps.decks.infrastructure.schemas import IndexDefinitions

from .conftest import run_async


def _save_card(owner_id, deck_id, front="network"):
    return run_async(CardRepository().save(Card(
        front=Word(front),
        back=Translation("rede"),
        front_description="The network is stable today.",
        back_description="A rede está estável durante o dia.",
        owner_id=owner_id,
        deck_id=deck_id,
    )))


def _save_review(card, owner_id, rating, reviewed_at=None):
    return run_async(CardReviewRepository().save(CardReview(
        card_id=card.id,
        deck_id=card.deck_id,
        owner_id=owner_id,
        rating=rating,
        reviewed_at=reviewed_at or datetime.now(timezone.utc),
    )))


@pytest.mark.django_db
def test_deck_statistics_return_all_time_rating_distribution(client_a, owner_a):
    owner_id = str(owner_a.id)
    deck = run_async(DeckRepository().save(Deck(
        title="Deck com histórico",
        owner_id=owner_id,
        daily_review_goal=8,
    )))
    card = _save_card(owner_id, deck.id)
    _save_review(card, owner_id, "again", datetime.now(timezone.utc) - timedelta(days=20))
    _save_review(card, owner_id, "hard")
    _save_review(card, owner_id, "good")
    _save_review(card, owner_id, "good")
    _save_review(card, owner_id, "easy")

    response = client_a.get(f"/api/v1/decks/{deck.id}/statistics/")

    assert response.status_code == 200
    assert response.data == {
        "rating_distribution": {"again": 1, "hard": 1, "good": 2, "easy": 1},
        "reviewed_today": 4,
        "daily_review_goal": 8,
        "goal_progress_percentage": 50,
    }


@pytest.mark.django_db
def test_deck_statistics_are_zeroed_without_reviews(client_a, owner_a):
    deck = run_async(DeckRepository().save(Deck(
        title="Deck sem histórico",
        owner_id=str(owner_a.id),
    )))

    response = client_a.get(f"/api/v1/decks/{deck.id}/statistics/")

    assert response.status_code == 200
    assert response.data == {
        "rating_distribution": {"again": 0, "hard": 0, "good": 0, "easy": 0},
        "reviewed_today": 0,
        "daily_review_goal": None,
        "goal_progress_percentage": None,
    }


@pytest.mark.django_db
def test_deck_statistics_hide_another_tenants_deck(client_a, owner_b):
    deck = run_async(DeckRepository().save(Deck(
        title="Deck privado",
        owner_id=str(owner_b.id),
    )))

    response = client_a.get(f"/api/v1/decks/{deck.id}/statistics/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_deck_statistics_exclude_reviews_from_soft_deleted_cards(client_a, owner_a):
    owner_id = str(owner_a.id)
    deck = run_async(DeckRepository().save(Deck(title="Deck ativo", owner_id=owner_id)))
    active_card = _save_card(owner_id, deck.id, "active")
    deleted_card = _save_card(owner_id, deck.id, "deleted")
    _save_review(active_card, owner_id, "easy")
    _save_review(deleted_card, owner_id, "again")
    run_async(CardRepository().delete(deleted_card.id, owner_id))

    response = client_a.get(f"/api/v1/decks/{deck.id}/statistics/")

    assert response.status_code == 200
    assert response.data["rating_distribution"] == {
        "again": 0,
        "hard": 0,
        "good": 0,
        "easy": 1,
    }


def test_card_review_indexes_cover_deck_statistics_query():
    assert ([
        ("owner_id", 1),
        ("deck_id", 1),
        ("reviewed_at", 1),
    ], {}) in IndexDefinitions.CARD_REVIEWS_INDEXES
