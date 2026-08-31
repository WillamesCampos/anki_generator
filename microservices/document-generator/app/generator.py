"""
Geração de deck `.apkg` compatível com o Anki, com áudio via gTTS.

Refatorado a partir do script standalone `generator_v2.py` (raiz do projeto
antes da Sprint 0): a lógica que antes era uma lista de cards hardcoded virou
uma função parametrizada, reutilizável pelo endpoint de exportação deste
microsserviço (ver `<funcionalidade id="exportacao-anki">` em
PROMPT_REFINADO.md). A integração completa com o Django (payload/contrato,
circuit breaker) é feita na Sprint 4 do PRD — aqui só a lógica de geração.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from genanki import Deck, Model, Note, Package
from gtts import gTTS

CARD_MODEL_FIELDS = [
    {"name": "Front"},
    {"name": "Back"},
    {"name": "FrontDescription"},
    {"name": "BackDescription"},
    {"name": "Notes"},
    {"name": "Audio"},
]

CARD_MODEL_TEMPLATE = [
    {
        "name": "Card 1",
        "qfmt": "{{Front}}<br>{{Audio}}",
        "afmt": """
            <b>Verso:</b> {{Back}}<br><br>
            <b>Descrição da frente:</b> {{FrontDescription}}<br>
            <b>Descrição do verso:</b> {{BackDescription}}<br><br>
            <b>Observações:</b> {{Notes}}
        """,
    }
]


@dataclass
class CardInput:
    front: str
    back: str
    front_description: str
    back_description: str
    notes: str = ""


def _build_model() -> Model:
    model_id = int(str(uuid.uuid4().int)[:9])
    return Model(
        model_id,
        "Anki Generator Card Model",
        fields=CARD_MODEL_FIELDS,
        templates=CARD_MODEL_TEMPLATE,
    )


def generate_deck_package(
    deck_title: str,
    cards: list[CardInput],
    output_dir: Path,
) -> Path:
    """
    Gera um pacote `.apkg` com áudio para cada card e devolve o caminho do arquivo.

    Args:
        deck_title: título do deck no Anki.
        cards: cards a incluir no deck (não pode ser vazio).
        output_dir: diretório onde o `.apkg` e os áudios temporários são gravados.

    Raises:
        ValueError: se `cards` estiver vazio.
    """
    if not cards:
        raise ValueError("cards cannot be empty")

    output_dir.mkdir(parents=True, exist_ok=True)
    audio_dir = output_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    model = _build_model()
    deck_id = int(str(uuid.uuid4().int)[:10])
    deck = Deck(deck_id, deck_title)
    media_files: list[str] = []

    for card in cards:
        audio_filename = f"{uuid.uuid4().hex}.mp3"
        audio_path = audio_dir / audio_filename

        tts = gTTS(card.front, lang="en", tld="com")
        tts.save(str(audio_path))
        media_files.append(str(audio_path))

        note = Note(
            model=model,
            fields=[
                card.front,
                card.back,
                card.front_description,
                card.back_description,
                card.notes,
                f"[sound:{audio_filename}]",
            ],
        )
        deck.add_note(note)

    safe_title = "".join(c if c.isalnum() else "_" for c in deck_title.lower())
    output_path = output_dir / f"{safe_title}_{datetime.now().strftime('%d-%m-%Y')}.apkg"
    Package(deck, media_files).write_to_file(str(output_path))

    return output_path
