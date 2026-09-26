"""Payload de exportação e hash de conteúdo (Sprint 11, D7).

O hash é calculado sobre exatamente o objeto que vai pro `document-generator`
— um builder só —, então nada exportável pode mudar sem mudar o hash, e o
estado FSRS (que não vai no `.apkg`) nunca invalida o cache."""

import copy
import uuid
from datetime import datetime, timedelta, timezone

from apps.decks.domain.entities.card import Card
from apps.decks.domain.entities.deck import Deck
from apps.decks.domain.services import export_payload
from apps.decks.domain.services.export_payload import (
    build_export_payload,
    compute_content_hash,
)
from apps.decks.domain.value_objects.translation import Translation
from apps.decks.domain.value_objects.word import Word

OWNER = "42"
T0 = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)


def make_deck(title="Inglês básico"):
    return Deck(title=title, owner_id=OWNER)


def make_card(deck, front="hello", back="olá", minutes=0, card_id=None):
    return Card(
        id=card_id or uuid.uuid4(),
        front=Word(front),
        back=Translation(back),
        front_description="Hello, how are you today?",
        back_description="Olá, como você está hoje?",
        owner_id=OWNER,
        deck_id=deck.id,
        created_at=T0 + timedelta(minutes=minutes),
    )


def test_payload_has_deck_identity_and_only_exportable_card_fields():
    deck = make_deck()
    card = make_card(deck)

    payload = build_export_payload(deck, [card])

    assert payload == {
        "deck_id": str(deck.id),
        "deck_title": "Inglês básico",
        "cards": [
            {
                "id": str(card.id),
                "front": "hello",
                "back": "olá",
                "front_description": "Hello, how are you today?",
                "back_description": "Olá, como você está hoje?",
            }
        ],
    }


def test_payload_never_carries_tenant_or_scheduling_data():
    deck = make_deck()
    payload = build_export_payload(deck, [make_card(deck)])

    serialized = repr(payload)
    for forbidden in (
        "owner_id",
        OWNER + "'",
        "stability",
        "difficulty",
        "due_at",
        "fsrs",
    ):
        assert forbidden not in serialized


def test_cards_are_ordered_deterministically_regardless_of_input_order():
    deck = make_deck()
    older = make_card(deck, front="first", minutes=0)
    newer = make_card(deck, front="second", minutes=5)

    a = build_export_payload(deck, [older, newer])
    b = build_export_payload(deck, [newer, older])

    assert a == b
    assert [c["front"] for c in a["cards"]] == ["first", "second"]


def test_same_content_gives_the_same_hash():
    deck = make_deck()
    cards = [make_card(deck, minutes=0), make_card(deck, front="bye", minutes=1)]

    h1 = compute_content_hash(build_export_payload(deck, cards))
    h2 = compute_content_hash(build_export_payload(deck, list(reversed(cards))))

    assert h1 == h2
    assert len(h1) == 64  # sha256 hex


def test_editing_any_exportable_field_changes_the_hash():
    deck = make_deck()
    card = make_card(deck)
    base = compute_content_hash(build_export_payload(deck, [card]))

    for attribute, new_value in [
        ("front", Word("hello there")),
        ("back", Translation("oi")),
        ("front_description", "A different front description."),
        ("back_description", "Uma descrição diferente do verso."),
    ]:
        edited = copy.deepcopy(card)
        setattr(edited, attribute, new_value)
        assert (
            compute_content_hash(build_export_payload(deck, [edited])) != base
        ), attribute


def test_renaming_adding_or_removing_cards_changes_the_hash():
    deck = make_deck()
    card = make_card(deck)
    extra = make_card(deck, front="bye", minutes=1)
    base = compute_content_hash(build_export_payload(deck, [card]))

    renamed = make_deck("Outro título")
    renamed.id = deck.id

    assert compute_content_hash(build_export_payload(renamed, [card])) != base
    assert compute_content_hash(build_export_payload(deck, [card, extra])) != base
    assert compute_content_hash(build_export_payload(deck, [])) != base


def test_spaced_repetition_state_does_not_change_the_hash():
    deck = make_deck()
    card = make_card(deck)
    base = compute_content_hash(build_export_payload(deck, [card]))

    card.stability = 12.5
    card.difficulty = 6.1
    card.fsrs_state = 2
    card.due_at = T0 + timedelta(days=9)
    card.last_reviewed_at = T0 + timedelta(days=1)
    card.updated_at = T0 + timedelta(days=1)

    assert compute_content_hash(build_export_payload(deck, [card])) == base


def test_hash_covers_the_whole_payload_so_a_new_field_cannot_be_forgotten():
    deck = make_deck()
    payload = build_export_payload(deck, [make_card(deck)])
    base = compute_content_hash(payload)

    top_level = copy.deepcopy(payload)
    top_level["new_top_level_field"] = "x"
    per_card = copy.deepcopy(payload)
    per_card["cards"][0]["new_card_field"] = "x"

    assert compute_content_hash(top_level) != base
    assert compute_content_hash(per_card) != base


def test_bumping_the_export_format_version_invalidates_every_hash(monkeypatch):
    deck = make_deck()
    payload = build_export_payload(deck, [make_card(deck)])
    before = compute_content_hash(payload)

    monkeypatch.setattr(export_payload, "EXPORT_FORMAT_VERSION", 2)

    assert compute_content_hash(payload) != before
