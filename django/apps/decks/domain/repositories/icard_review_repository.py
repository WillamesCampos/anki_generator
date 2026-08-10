"""
Interface ICardReviewRepository - Define operações de persistência para
CardReview (um documento por evento de revisão, ver D5 em
openspec/changes/sprint-2-decks-cards/design.md).
"""

import uuid
from abc import ABC, abstractmethod
from typing import List
from ..entities.card_review import CardReview


class ICardReviewRepository(ABC):
    """Interface para repositório de CardReview."""

    @abstractmethod
    async def save(self, review: CardReview) -> CardReview:
        pass

    @abstractmethod
    async def find_by_card_id(self, card_id: uuid.UUID, owner_id: str) -> List[CardReview]:
        pass
