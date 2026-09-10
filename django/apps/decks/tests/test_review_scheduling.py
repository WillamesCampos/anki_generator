"""
Registro de revisão (PRD Sprint 2, 2.2/2.3) — dispara o agendamento FSRS
(domain/services/scheduling_service.py) e grava um `CardReview` (D4/D5 em
openspec/changes/sprint-2-decks-cards/design.md), além da consulta de
cards devidos.
"""

from datetime import datetime, timedelta, timezone

import pytest

from apps.decks.domain.entities.card import Card
from apps.decks.domain.entities.deck import Deck
from apps.decks.domain.value_objects.translation import Translation
from apps.decks.domain.value_objects.word import Word
from apps.decks.infrastructure.repositories.card_repository import CardRepository
from apps.decks.infrastructure.repositories.deck_repository import DeckRepository


def _build_card(owner_id, deck_id, front="cache") -> Card:
    return Card(
        front=Word(front),
        back=Translation("traducao"),
        front_description="This is an example sentence here.",
        back_description="Esta eh uma frase de exemplo aqui.",
        owner_id=owner_id,
        deck_id=deck_id,
    )


@pytest.mark.django_db
def test_review_action_updates_schedule_and_creates_review(client_a, owner_a):
    owner_id = str(owner_a.id)
    deck = DeckRepository().save(Deck(title="Deck Review", owner_id=owner_id))

    card = CardRepository().save(_build_card(owner_id, deck.id))

    assert card.stability is None

    response = client_a.post(
        f"/api/v1/cards/{card.id}/review/", {"rating": "good"}, format="json"
    )

    assert response.status_code == 201
    assert response.data["rating"] == "good"
    assert response.data["card_id"] == str(card.id)
    assert response.data["stability_after"] is not None

    updated_card = CardRepository().find_by_id(card.id, owner_id)
    assert updated_card.stability == response.data["stability_after"]
    assert updated_card.last_reviewed_at is not None


@pytest.mark.django_db
def test_review_rejects_invalid_rating(client_a, owner_a):
    owner_id = str(owner_a.id)
    deck = DeckRepository().save(Deck(title="Deck Review 2", owner_id=owner_id))

    card = CardRepository().save(_build_card(owner_id, deck.id, front="token"))

    response = client_a.post(
        f"/api/v1/cards/{card.id}/review/", {"rating": "excellent"}, format="json"
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_review_on_other_owner_card_returns_404(client_a, client_b, owner_b):
    owner_id_b = str(owner_b.id)
    deck = DeckRepository().save(Deck(title="Deck B", owner_id=owner_id_b))
    card = CardRepository().save(_build_card(owner_id_b, deck.id, front="secret"))

    response = client_a.post(
        f"/api/v1/cards/{card.id}/review/", {"rating": "good"}, format="json"
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_due_cards_only_returns_owned_and_due(owner_a, owner_b):
    owner_id_a, owner_id_b = str(owner_a.id), str(owner_b.id)
    deck_a = DeckRepository().save(Deck(title="Deck A", owner_id=owner_id_a))
    deck_b = DeckRepository().save(Deck(title="Deck B", owner_id=owner_id_b))

    due_card = _build_card(owner_id_a, deck_a.id, front="duecard")
    due_card.due_at = datetime.now(timezone.utc) - timedelta(days=1)
    due_card = CardRepository().save(due_card)

    future_card = _build_card(owner_id_a, deck_a.id, front="futurecard")
    future_card.due_at = datetime.now(timezone.utc) + timedelta(days=10)
    future_card = CardRepository().save(future_card)

    other_owner_due_card = _build_card(owner_id_b, deck_b.id, front="otherowner")
    other_owner_due_card.due_at = datetime.now(timezone.utc) - timedelta(days=1)
    other_owner_due_card = CardRepository().save(other_owner_due_card)

    due_ids = {str(c.id) for c in CardRepository().find_due(owner_id_a)}

    assert str(due_card.id) in due_ids
    assert str(future_card.id) not in due_ids
    assert str(other_owner_due_card.id) not in due_ids
