"""
Geração de deck `.apkg` compatível com o Anki, com áudio via gTTS.

Refatorado a partir do script standalone `generator_v2.py` (raiz do projeto
antes da Sprint 0): a lógica que antes era uma lista de cards hardcoded virou
uma função parametrizada, reutilizável pelo endpoint de exportação deste
microsserviço (ver `<funcionalidade id="exportacao-anki">` em
PROMPT_REFINADO.md). A integração completa com o Django (contrato, cache, circuit
breaker) é da Sprint 11 do PRD — aqui só a lógica de geração.
"""

import hashlib
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from genanki import Deck, Model, Note, Package, guid_for
from gtts import gTTS

# Versão do formato do pacote (campos/template do modelo). Sobe junto com
# `MODEL_ID` se o template ou os campos mudarem — o Django inclui uma
# constante equivalente no hash de conteúdo pra invalidar exportações antigas
# (Sprint 11, D7/D8).
EXPORT_FORMAT_VERSION = 1

# ID do note type "Anki Generator Card Model": fixo, pra reimportar um deck
# atualizar as notas em vez de criar um note type novo a cada exportação.
# Faixa recomendada pelo genanki: [1 << 30, 1 << 31).
MODEL_ID = 1_607_392_319

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
    id: str
    front: str
    back: str
    front_description: str
    back_description: str
    notes: str = ""


def _audio_filename(front: str) -> str:
    """Nome determinístico a partir do texto da frente (e do idioma fixo do
    TTS) — reimportar o mesmo texto não empilha arquivos de mídia órfãos."""
    return f"tts_{hashlib.sha1(front.encode()).hexdigest()}.mp3"


def stable_deck_id(deck_id: str) -> int:
    """ID de deck do Anki derivado deterministicamente do UUID do deck
    (Sprint 11, D8): o mesmo deck sempre gera o mesmo ID, então reimportar
    atualiza o deck existente. Faixa `[1 << 30, 1 << 31)` recomendada pelo
    genanki; 2^30 valores tornam colisão entre decks do mesmo usuário
    desprezível."""
    digest = hashlib.sha256(str(deck_id).encode()).digest()
    return (1 << 30) + int.from_bytes(digest[:8], "big") % (1 << 30)


def _build_model() -> Model:
    return Model(
        MODEL_ID,
        "Anki Generator Card Model",
        fields=CARD_MODEL_FIELDS,
        templates=CARD_MODEL_TEMPLATE,
    )


def generate_deck_package(
    deck_id: str,
    deck_title: str,
    cards: list[CardInput],
    output_dir: Path,
) -> Path:
    """
    Gera um pacote `.apkg` com áudio para cada card e devolve o caminho do arquivo.

    Args:
        deck_id: UUID do deck de origem — o ID do deck no Anki é derivado
            dele, estável entre exportações.
        deck_title: título do deck no Anki.
        cards: cards a incluir no deck (não pode ser vazio).
        output_dir: diretório-base. Cada chamada cria dentro dele um diretório
            de trabalho só seu (`<output_dir>/<uuid>/`) — o chamador é
            responsável por removê-lo (`shutil.rmtree(path.parent)`) depois de
            usar o arquivo. Numa falha, o diretório é removido aqui mesmo.

    Returns:
        Caminho do `.apkg`, dentro do diretório de trabalho da chamada.

    Raises:
        ValueError: se `cards` estiver vazio.
    """
    if not cards:
        raise ValueError("cards cannot be empty")

    # Diretório único por chamada (Sprint 11, D10): duas exportações —
    # inclusive de decks com o mesmo título — nunca compartilham arquivo.
    work_dir = output_dir / uuid.uuid4().hex
    audio_dir = work_dir / "audio"
    audio_dir.mkdir(parents=True)

    try:
        return _build_package(deck_id, deck_title, cards, work_dir, audio_dir)
    except BaseException:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise


def _build_package(
    deck_id: str,
    deck_title: str,
    cards: list[CardInput],
    work_dir: Path,
    audio_dir: Path,
) -> Path:
    model = _build_model()
    deck = Deck(stable_deck_id(deck_id), deck_title)
    media_files: list[str] = []
    generated_audio: set[str] = set()

    for card in cards:
        audio_filename = _audio_filename(card.front)
        audio_path = audio_dir / audio_filename

        # Mesmo texto de frente => mesmo arquivo: uma chamada de rede só e
        # sem mídia duplicada no pacote (Sprint 11, D8).
        if audio_filename not in generated_audio:
            tts = gTTS(card.front, lang="en", tld="com")
            tts.save(str(audio_path))
            media_files.append(str(audio_path))
            generated_audio.add(audio_filename)

        note = Note(
            model=model,
            guid=guid_for(card.id),
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
    output_path = work_dir / f"{safe_title}_{datetime.now().strftime('%d-%m-%Y')}.apkg"
    Package(deck, media_files).write_to_file(str(output_path))

    return output_path
