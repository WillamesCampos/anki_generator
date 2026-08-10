"""
Interface IDeckRepository - Define operações de persistência para Decks

Toda operação de leitura/escrita que localiza um deck por ID ou por outro
filtro exige `owner_id` como parâmetro obrigatório, embutido diretamente no
filtro da consulta (ver D1 em
openspec/changes/sprint-2-decks-cards/design.md).
"""

import uuid
from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.deck import Deck


class IDeckRepository(ABC):
    """Interface para repositório de Decks."""

    @abstractmethod
    async def save(self, deck: Deck) -> Deck:
        """Salva um deck (owner_id já vem embutido na entidade)."""
        pass

    @abstractmethod
    async def find_by_id(self, deck_id: uuid.UUID, owner_id: str) -> Optional[Deck]:
        pass

    @abstractmethod
    async def find_by_title(self, title: str, owner_id: str) -> List[Deck]:
        pass

    @abstractmethod
    async def find_all(self, owner_id: str, skip: int = 0, limit: int = 100) -> List[Deck]:
        pass

    @abstractmethod
    async def find_by_user_id(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Deck]:
        pass

    @abstractmethod
    async def update(self, deck: Deck) -> Deck:
        """Atualiza um deck (filtro embute `_id` + `deck.owner_id`)."""
        pass

    @abstractmethod
    async def delete(self, deck_id: uuid.UUID, owner_id: str) -> bool:
        pass

    @abstractmethod
    async def count(self, owner_id: str) -> int:
        pass

    @abstractmethod
    async def count_by_user_id(self, user_id: str) -> int:
        pass

    @abstractmethod
    async def exists(self, deck_id: uuid.UUID, owner_id: str) -> bool:
        pass

    @abstractmethod
    async def exists_by_title(self, title: str, owner_id: str) -> bool:
        pass
