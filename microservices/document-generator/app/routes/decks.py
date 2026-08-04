from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.config import get_settings
from app.errors import ValidationError
from app.generator import CardInput, generate_deck_package

router = APIRouter(prefix="/decks", tags=["Decks"])


class CardPayload(BaseModel):
    term: str
    translation: str
    example: str
    example_translation: str
    notes: str = ""


class ExportDeckRequest(BaseModel):
    deck_title: str
    cards: list[CardPayload] = Field(default_factory=list)


@router.post("/export")
async def export_deck(payload: ExportDeckRequest) -> FileResponse:
    """Gera e devolve um `.apkg` a partir dos cards enviados."""
    if not payload.cards:
        raise ValidationError("At least one card is required to export a deck")

    settings = get_settings()
    cards = [CardInput(**card.model_dump()) for card in payload.cards]
    output_path = generate_deck_package(
        deck_title=payload.deck_title,
        cards=cards,
        output_dir=Path(settings.audio_output_dir),
    )

    return FileResponse(
        path=output_path,
        filename=output_path.name,
        media_type="application/octet-stream",
    )
