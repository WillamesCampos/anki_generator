"""
Serviço de agendamento de repetição espaçada via FSRS.

Encapsula o pacote `fsrs` (ver D4 em
openspec/changes/sprint-2-decks-cards/design.md): nenhum outro módulo do
domínio importa `fsrs` diretamente — se o algoritmo for trocado no futuro,
a mudança fica isolada aqui.
"""

from datetime import datetime, timezone
from typing import Optional

import fsrs

from ..entities.card import Card
from ..exceptions import DomainValidationError

_scheduler = fsrs.Scheduler()

_RATING_MAP = {
    "again": fsrs.Rating.Again,
    "hard": fsrs.Rating.Hard,
    "good": fsrs.Rating.Good,
    "easy": fsrs.Rating.Easy,
}


def review_card(card: Card, rating: str, reviewed_at: Optional[datetime] = None) -> Card:
    """
    Aplica uma revisão ao card, recalculando seus campos de agendamento FSRS
    em memória (não persiste — quem chama decide quando salvar via
    repositório).
    """
    if rating not in _RATING_MAP:
        raise DomainValidationError(f"Invalid rating: {rating!r}. Must be one of {sorted(_RATING_MAP)}")

    reviewed_at = reviewed_at or datetime.now(timezone.utc)

    fsrs_card = fsrs.Card(
        state=fsrs.State(card.fsrs_state),
        step=card.fsrs_step,
        stability=card.stability,
        difficulty=card.difficulty,
        due=card.due_at,
        last_review=card.last_reviewed_at,
    )

    updated_fsrs_card, _review_log = _scheduler.review_card(
        fsrs_card, _RATING_MAP[rating], review_datetime=reviewed_at
    )

    card.fsrs_state = int(updated_fsrs_card.state)
    card.fsrs_step = updated_fsrs_card.step
    card.stability = updated_fsrs_card.stability
    card.difficulty = updated_fsrs_card.difficulty
    card.due_at = updated_fsrs_card.due
    card.last_reviewed_at = updated_fsrs_card.last_review
    card.updated_at = datetime.now(timezone.utc)

    return card
