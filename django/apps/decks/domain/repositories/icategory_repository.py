"""
Interface ICategoryRepository - Define operações de persistência para Category

Mesmo padrão de owner_id obrigatório dos demais repositórios (ver D1/D6 em
openspec/changes/sprint-2-decks-cards/design.md).
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from ..entities.category import Category


class ICategoryRepository(ABC):
    """Interface para repositório de Categories."""

    @abstractmethod
    def save(self, category: Category) -> Category:
        pass

    @abstractmethod
    def find_by_id(self, category_id: uuid.UUID, owner_id: str) -> Optional[Category]:
        pass

    @abstractmethod
    def find_all(self, owner_id: str) -> List[Category]:
        pass

    @abstractmethod
    def update(self, category: Category) -> Category:
        pass

    @abstractmethod
    def delete(self, category_id: uuid.UUID, owner_id: str) -> bool:
        """Soft delete (Sprint 6) — marca `deleted_at` e desvincula (não cascateia) os decks que a referenciam."""
        pass

    @abstractmethod
    def exists(self, category_id: uuid.UUID, owner_id: str) -> bool:
        pass

    @abstractmethod
    def purge_soft_deleted(self, older_than: datetime) -> int:
        """Remove fisicamente categorias com `deleted_at` anterior a `older_than` (Sprint 6, purge job)."""
        pass
