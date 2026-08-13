"""
Entidade CardReview - Um evento de revisão de um card (Sprint 2, PRD 2.3).

Granularidade de um evento por revisão (não uma "sessão" agregada) — mesma
granularidade que o Anki real usa internamente (tabela `revlog`). É uma
entidade própria, deliberadamente distinta de `GenerationSession` (que
representa um job de geração de cards via IA, do protótipo antigo, e
continua inalterada). Ver D5 em
openspec/changes/sprint-2-decks-cards/design.md.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, field
from ..exceptions import DomainValidationError

VALID_RATINGS = {"again", "hard", "good", "easy"}


@dataclass
class CardReview:
    """
    Entidade CardReview representa um único evento de revisão de um card,
    junto com o resultado do agendamento FSRS após essa revisão.
    """

    card_id: uuid.UUID
    owner_id: str
    rating: str

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    reviewed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Snapshot do agendamento do Card logo após esta revisão (ver
    # domain/services/scheduling_service.py)
    stability_after: Optional[float] = None
    difficulty_after: Optional[float] = None
    due_at_after: Optional[datetime] = None

    # Denormalizado a partir de Card.deck_id no momento da revisão — evita
    # a SPA precisar de um GET /cards/{id}/ só pra descobrir o deck (Sprint 3:
    # "último deck estudado" virou 2 requests em cadeia, o suficiente pra
    # estourar o throttle de 3 req/s sob o double-effect do StrictMode em
    # dev). deck_id é uma referência estável (nunca muda), diferente de um
    # título/nome de deck — por isso é seguro denormalizar isso e só isso,
    # sem risco de ficar desatualizado se o deck for renomeado depois.
    deck_id: Optional[uuid.UUID] = None

    def __post_init__(self):
        self._validate_card_review()

    def _validate_card_review(self) -> None:
        if not self.owner_id or not str(self.owner_id).strip():
            raise DomainValidationError("owner_id cannot be empty")

        if self.card_id is None:
            raise DomainValidationError("card_id cannot be None")

        if self.rating not in VALID_RATINGS:
            raise DomainValidationError(f"rating must be one of {sorted(VALID_RATINGS)}, got {self.rating!r}")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "card_id": str(self.card_id),
            "owner_id": self.owner_id,
            "rating": self.rating,
            "reviewed_at": self.reviewed_at.isoformat(),
            "stability_after": self.stability_after,
            "difficulty_after": self.difficulty_after,
            "due_at_after": self.due_at_after.isoformat() if self.due_at_after else None,
            "deck_id": str(self.deck_id) if self.deck_id else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CardReview":
        return cls(
            id=uuid.UUID(data["id"]),
            card_id=uuid.UUID(data["card_id"]),
            owner_id=data["owner_id"],
            rating=data["rating"],
            reviewed_at=datetime.fromisoformat(data["reviewed_at"]),
            stability_after=data.get("stability_after"),
            difficulty_after=data.get("difficulty_after"),
            due_at_after=datetime.fromisoformat(data["due_at_after"]) if data.get("due_at_after") else None,
            deck_id=uuid.UUID(data["deck_id"]) if data.get("deck_id") else None,
        )

    def __str__(self) -> str:
        return f"CardReview(card_id={self.card_id}, rating='{self.rating}')"

    def __repr__(self) -> str:
        return f"CardReview(id={self.id}, card_id={self.card_id}, rating='{self.rating}', reviewed_at={self.reviewed_at})"
