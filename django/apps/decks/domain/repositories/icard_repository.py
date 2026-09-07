"""
Interface ICardRepository - Define operações de persistência para Cards

Toda operação de leitura/escrita que localiza um card por ID ou por outro
filtro exige `owner_id` como parâmetro obrigatório, embutido diretamente no
filtro da consulta — nunca conferido depois em Python (ver D1 em
openspec/changes/sprint-2-decks-cards/design.md, `<ponto_critico
id="isolamento-multi-tenant">` em PROMPT_REFINADO.md).
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from ..entities.card import Card


class ICardRepository(ABC):
    """Interface para repositório de Cards."""

    @abstractmethod
    async def save(self, card: Card) -> Card:
        """Salva um card (owner_id já vem embutido na entidade)."""
        pass

    @abstractmethod
    async def save_many(self, cards: List[Card]) -> List[Card]:
        """Salva múltiplos cards (owner_id já vem embutido em cada entidade)."""
        pass

    @abstractmethod
    async def find_by_id(self, card_id: uuid.UUID, owner_id: str) -> Optional[Card]:
        pass

    @abstractmethod
    async def find_by_front(self, front: str, owner_id: str) -> List[Card]:
        pass

    @abstractmethod
    async def find_by_deck_id(self, deck_id: uuid.UUID, owner_id: str) -> List[Card]:
        pass

    @abstractmethod
    async def find_by_context(self, context: str, owner_id: str) -> List[Card]:
        pass

    @abstractmethod
    async def find_similar_cards(
        self, front: str, owner_id: str, similarity_threshold: float = 0.8
    ) -> List[Card]:
        pass

    @abstractmethod
    async def find_duplicates(self, card: Card, owner_id: str) -> List[Card]:
        pass

    @abstractmethod
    async def find_due(
        self, owner_id: str, due_before: Optional[datetime] = None
    ) -> List[Card]:
        """Cards devidos (`due_at <= due_before`, default agora) para um owner."""
        pass

    @abstractmethod
    async def update(self, card: Card) -> Card:
        """Atualiza um card (filtro embute `_id` + `card.owner_id`)."""
        pass

    @abstractmethod
    async def delete(self, card_id: uuid.UUID, owner_id: str) -> bool:
        """Soft delete (Sprint 6) — marca `deleted_at`, não remove fisicamente."""
        pass

    @abstractmethod
    async def delete_by_deck_id(self, deck_id: uuid.UUID, owner_id: str) -> int:
        """Soft delete de todos os cards do deck (Sprint 6) — cascade a partir de `DeckRepository.delete()`."""
        pass

    @abstractmethod
    async def count(self, owner_id: str) -> int:
        pass

    @abstractmethod
    async def count_by_deck_id(self, deck_id: uuid.UUID, owner_id: str) -> int:
        pass

    @abstractmethod
    async def exists(self, card_id: uuid.UUID, owner_id: str) -> bool:
        pass

    @abstractmethod
    async def exists_by_front(
        self, front: str, owner_id: str, deck_id: Optional[uuid.UUID] = None
    ) -> bool:
        pass

    @abstractmethod
    async def purge_soft_deleted(self, older_than: datetime) -> int:
        """Remove fisicamente cards com `deleted_at` anterior a `older_than` (Sprint 6, purge job)."""
        pass
