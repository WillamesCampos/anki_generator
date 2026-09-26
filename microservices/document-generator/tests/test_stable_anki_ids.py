"""IDs estáveis no `.apkg` (Sprint 11, D8): exportar o mesmo deck de novo,
com conteúdo editado, precisa manter o mesmo deck/modelo/guids pro Anki
atualizar o deck existente em vez de duplicá-lo ao reimportar."""

import uuid

from app.generator import CardInput, generate_deck_package
from tests.apkg_helpers import read_apkg

DECK_A = uuid.UUID("0b0f0b1e-6f6d-4d8e-9c47-2f1f5f0a1111")
DECK_B = uuid.UUID("0b0f0b1e-6f6d-4d8e-9c47-2f1f5f0a2222")
CARD_1 = uuid.UUID("c1a1c1a1-0000-4000-8000-000000000001")
CARD_2 = uuid.UUID("c1a1c1a1-0000-4000-8000-000000000002")


def make_card(card_id, front="hello", back="olá"):
    return CardInput(
        id=str(card_id),
        front=front,
        back=back,
        front_description="Hello, how are you?",
        back_description="Olá, como vai você?",
    )


def export(deck_id, cards, tmp_path, title="Deck"):
    path = generate_deck_package(
        deck_id=str(deck_id), deck_title=title, cards=cards, output_dir=tmp_path
    )
    return read_apkg(path)


def test_same_deck_exported_twice_keeps_deck_and_model_ids(tmp_path):
    first = export(DECK_A, [make_card(CARD_1)], tmp_path)
    second = export(DECK_A, [make_card(CARD_1, back="oi (editado)")], tmp_path)

    assert first["deck_ids"] == second["deck_ids"]
    assert first["model_ids"] == second["model_ids"]


def test_note_guid_is_stable_per_card_id_even_when_content_changes(tmp_path):
    first = export(DECK_A, [make_card(CARD_1), make_card(CARD_2, front="bye")], tmp_path)
    second = export(
        DECK_A, [make_card(CARD_1, front="hello!!"), make_card(CARD_2, front="bye")], tmp_path
    )

    assert [n["guid"] for n in first["notes"]] == [n["guid"] for n in second["notes"]]
    assert len({n["guid"] for n in first["notes"]}) == 2


def test_different_decks_get_different_deck_ids(tmp_path):
    a = export(DECK_A, [make_card(CARD_1)], tmp_path)
    b = export(DECK_B, [make_card(CARD_1)], tmp_path)

    assert a["deck_ids"] != b["deck_ids"]


def test_deck_id_stays_in_the_range_genanki_recommends(tmp_path):
    exported = export(DECK_A, [make_card(CARD_1)], tmp_path)

    assert all(1 << 30 <= deck_id < 1 << 31 for deck_id in exported["deck_ids"])
    assert all(1 << 30 <= model_id < 1 << 31 for model_id in exported["model_ids"])
