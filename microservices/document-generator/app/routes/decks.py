import shutil
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from pydantic import BaseModel, Field

from app.auth import require_service_jwt
from app.config import get_settings
from app.errors import ValidationError
from app.generator import CardInput, generate_deck_package

router = APIRouter(prefix="/decks", tags=["Decks"], dependencies=[Depends(require_service_jwt)])


class CardPayload(BaseModel):
    id: UUID
    front: str
    back: str
    front_description: str
    back_description: str
    notes: str = ""


class ExportDeckRequest(BaseModel):
    deck_id: UUID
    deck_title: str
    cards: list[CardPayload] = Field(default_factory=list)


@router.post("/export")
def export_deck(payload: ExportDeckRequest) -> FileResponse:
    """Gera e devolve um `.apkg` a partir dos cards enviados.

    Rota síncrona (`def`, não `async def`) de propósito: a geração é
    bloqueante (uma chamada de rede ao gTTS por card) e o FastAPI roda rotas
    `def` numa threadpool — com `async def` ela travaria o event loop inteiro,
    inclusive o health check (Sprint 11, D10).
    """
    if not payload.cards:
        raise ValidationError("At least one card is required to export a deck")

    settings = get_settings()
    if len(payload.cards) > settings.max_cards_per_export:
        raise ValidationError(
            f"A deck export is limited to {settings.max_cards_per_export} cards"
        )

    cards = [
        CardInput(**{**card.model_dump(), "id": str(card.id)}) for card in payload.cards
    ]
    output_path = generate_deck_package(
        deck_id=str(payload.deck_id),
        deck_title=payload.deck_title,
        cards=cards,
        output_dir=Path(settings.audio_output_dir),
    )

    return FileResponse(
        path=output_path,
        filename=output_path.name,
        media_type="application/octet-stream",
        # o diretório de trabalho é único por requisição — apagado depois que
        # a resposta foi enviada (nada acumula no volume)
        background=BackgroundTask(shutil.rmtree, output_path.parent, ignore_errors=True),
    )
