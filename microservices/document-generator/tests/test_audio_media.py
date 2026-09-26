"""Áudio do `.apkg` (Sprint 11, D8): nome de arquivo determinístico a partir
do texto da frente, sem duplicar mídia nem repetir chamadas de rede ao gTTS
pra um texto que já apareceu no mesmo deck."""

import uuid

from app.generator import generate_deck_package
from tests.apkg_helpers import read_apkg
from tests.test_stable_anki_ids import DECK_A, make_card

IDS = [uuid.UUID(int=i) for i in range(1, 4)]


def export(cards, tmp_path):
    path = generate_deck_package(
        deck_id=str(DECK_A), deck_title="Deck", cards=cards, output_dir=tmp_path
    )
    return read_apkg(path)


def test_audio_file_name_is_deterministic_for_the_same_front_text(tmp_path):
    first = export([make_card(IDS[0], front="hello")], tmp_path)
    second = export([make_card(IDS[0], front="hello")], tmp_path)

    assert first["media"] == second["media"]
    assert len(first["media"]) == 1


def test_different_front_texts_get_different_audio_files(tmp_path):
    exported = export(
        [make_card(IDS[0], front="hello"), make_card(IDS[1], front="goodbye")], tmp_path
    )

    assert len(set(exported["media"])) == 2


def test_cards_with_the_same_front_share_one_audio_file_and_one_tts_call(
    tmp_path, tts_calls
):
    exported = export(
        [make_card(IDS[0], front="hello"), make_card(IDS[1], front="hello")], tmp_path
    )

    assert len(exported["media"]) == 1
    assert tts_calls == ["hello"]
    assert len(exported["notes"]) == 2
    assert exported["notes"][0]["fields"][-1] == exported["notes"][1]["fields"][-1]
