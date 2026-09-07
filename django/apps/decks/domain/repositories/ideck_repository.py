"""
Interface IDeckRepository - Define operações de persistência para Decks

Toda operação de leitura/escrita que localiza um deck por ID ou por outro
filtro exige `owner_id` como parâmetro obrigatório, embutido diretamente no
filtro da consulta (ver D1 em
openspec/changes/sprint-2-decks-cards/design.md).
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
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
    async def find_all(
        self, owner_id: str, skip: int = 0, limit: int = 100
    ) -> List[Deck]:
        pass

    @abstractmethod
    async def update(self, deck: Deck) -> Deck:
        """Atualiza um deck (filtro embute `_id` + `deck.owner_id`)."""
        pass

    @abstractmethod
    async def delete(self, deck_id: uuid.UUID, owner_id: str) -> bool:
        """Soft delete (Sprint 6) — marca `deleted_at`, cascateia pros cards do deck."""
        pass

    @abstractmethod
    async def unlink_category(self, category_id: uuid.UUID, owner_id: str) -> int:
        """Zera `category_id` em todo deck que referencia essa categoria (Sprint 6, D6)."""
        pass

    @abstractmethod
    async def count(self, owner_id: str) -> int:
        pass

    @abstractmethod
    async def exists(self, deck_id: uuid.UUID, owner_id: str) -> bool:
        pass

    @abstractmethod
    async def exists_by_title(self, title: str, owner_id: str) -> bool:
        pass

    @abstractmethod
    async def purge_soft_deleted(self, older_than: datetime) -> int:
        """Remove fisicamente decks com `deleted_at` anterior a `older_than` (Sprint 6, purge job)."""
        pass
