"""
Interface ICategoryRepository - Define operações de persistência para Category

Mesmo padrão de owner_id obrigatório dos demais repositórios (ver D1/D6 em
openspec/changes/sprint-2-decks-cards/design.md).
"""

import uuid
from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.category import Category


class ICategoryRepository(ABC):
    """Interface para repositório de Categories."""

    @abstractmethod
    async def save(self, category: Category) -> Category:
        pass

    @abstractmethod
    async def find_by_id(self, category_id: uuid.UUID, owner_id: str) -> Optional[Category]:
        pass

    @abstractmethod
    async def find_all(self, owner_id: str) -> List[Category]:
        pass

    @abstractmethod
    async def update(self, category: Category) -> Category:
        pass

    @abstractmethod
    async def delete(self, category_id: uuid.UUID, owner_id: str) -> bool:
        pass

    @abstractmethod
    async def exists(self, category_id: uuid.UUID, owner_id: str) -> bool:
        pass
