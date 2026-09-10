"""
Interface ICardReviewRepository - Define operações de persistência para
CardReview (um documento por evento de revisão, ver D5 em
openspec/changes/sprint-2-decks-cards/design.md).
"""

import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from ..entities.card_review import CardReview


class ICardReviewRepository(ABC):
    """Interface para repositório de CardReview."""

    @abstractmethod
    def save(self, review: CardReview) -> CardReview:
        pass

    @abstractmethod
    def find_by_card_id(self, card_id: uuid.UUID, owner_id: str) -> List[CardReview]:
        pass

    @abstractmethod
    def find_by_owner(self, owner_id: str, limit: int = 100) -> List[CardReview]:
        """Revisões do owner, mais recentes primeiro — base da Home (Sprint 3: último deck estudado, gráfico de estatísticas)."""
        pass

    @abstractmethod
    def get_deck_statistics(self, owner_id: str, deck_id: uuid.UUID) -> Dict[str, Any]:
        """Agrega a distribuição histórica e as revisões de hoje de um deck ativo."""
        pass
