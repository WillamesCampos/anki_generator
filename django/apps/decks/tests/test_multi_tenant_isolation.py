"""
`<ponto_critico id="isolamento-multi-tenant">`: mesmo padrão de rigor da
Sprint 1, mas testado na camada onde ele realmente mora para decks/cards —
os repositórios Mongo (ver D1 em
openspec/changes/sprint-2-decks-cards/design.md), não um mixin de
QuerySet do Django ORM.
"""

import pytest

from apps.decks.domain.entities.card import Card
from apps.decks.domain.entities.card_review import CardReview
from apps.decks.domain.entities.category import Category
from apps.decks.domain.entities.deck import Deck
from apps.decks.domain.value_objects.translation import Translation
from apps.decks.domain.value_objects.word import Word
from apps.decks.infrastructure.repositories.card_repository import CardRepository
from apps.decks.infrastructure.repositories.card_review_repository import CardReviewRepository
from apps.decks.infrastructure.repositories.category_repository import CategoryRepository
from apps.decks.infrastructure.repositories.deck_repository import DeckRepository

from .conftest import run_async


def _build_card(owner_id, deck_id) -> Card:
    return Card(
        front=Word("network"),
        back=Translation("rede"),
        front_description="The network is down today.",
        back_description="A rede esta fora do ar hoje.",
        owner_id=owner_id,
        deck_id=deck_id,
    )


@pytest.mark.django_db
def test_deck_cross_tenant_access_is_blocked(owner_a, owner_b):
    owner_id_a, owner_id_b = str(owner_a.id), str(owner_b.id)

    deck = run_async(DeckRepository().save(Deck(title="Secreto", owner_id=owner_id_a)))

    assert run_async(DeckRepository().find_by_id(deck.id, owner_id_a)) is not None
    assert run_async(DeckRepository().find_by_id(deck.id, owner_id_b)) is None


@pytest.mark.django_db
def test_category_cross_tenant_access_is_blocked(owner_a, owner_b):
    owner_id_a, owner_id_b = str(owner_a.id), str(owner_b.id)

    category = run_async(CategoryRepository().save(Category(name="Trabalho", owner_id=owner_id_a)))

    assert run_async(CategoryRepository().find_by_id(category.id, owner_id_a)) is not None
    assert run_async(CategoryRepository().find_by_id(category.id, owner_id_b)) is None


@pytest.mark.django_db
def test_card_cross_tenant_access_is_blocked(owner_a, owner_b):
    owner_id_a, owner_id_b = str(owner_a.id), str(owner_b.id)

    deck = run_async(DeckRepository().save(Deck(title="Deck A", owner_id=owner_id_a)))
    card = run_async(CardRepository().save(_build_card(owner_id_a, deck.id)))

    assert run_async(CardRepository().find_by_id(card.id, owner_id_a)) is not None
    assert run_async(CardRepository().find_by_id(card.id, owner_id_b)) is None
    assert run_async(CardRepository().find_by_deck_id(deck.id, owner_id_b)) == []


@pytest.mark.django_db
def test_card_review_cross_tenant_access_is_blocked(owner_a, owner_b):
    owner_id_a, owner_id_b = str(owner_a.id), str(owner_b.id)

    deck = run_async(DeckRepository().save(Deck(title="Deck A", owner_id=owner_id_a)))
    card = run_async(CardRepository().save(_build_card(owner_id_a, deck.id)))
    run_async(CardReviewRepository().save(CardReview(card_id=card.id, owner_id=owner_id_a, rating="good")))

    own_reviews = run_async(CardReviewRepository().find_by_card_id(card.id, owner_id_a))
    other_reviews = run_async(CardReviewRepository().find_by_card_id(card.id, owner_id_b))

    assert len(own_reviews) == 1
    assert other_reviews == []
