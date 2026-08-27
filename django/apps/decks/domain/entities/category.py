"""
Entidade Category - Agrupa decks por categoria (Sprint 2, ver PRD 2.4).

Não existia no domínio migrado da Sprint 0 (protótipo antigo não tinha esse
conceito) — criada do zero seguindo o mesmo padrão de `Deck`/`Card`
(dataclass + owner_id obrigatório desde o primeiro campo, ver D6 em
openspec/changes/sprint-2-decks-cards/design.md).
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, field
from ..exceptions import DomainValidationError


@dataclass
class Category:
    """
    Entidade Category representa uma categoria de organização de decks.
    """

    name: str
    owner_id: str

    id: uuid.UUID = field(default_factory=uuid.uuid4)

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Auditoria (Sprint 5) — quem criou/alterou por último, preenchido pelo
    # serializer a partir da request autenticada, nunca aceito do cliente.
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    def __post_init__(self):
        self._validate_category()

    def _validate_category(self) -> None:
        if not self.name or not self.name.strip():
            raise DomainValidationError("Category name cannot be empty")

        if not self.owner_id or not str(self.owner_id).strip():
            raise DomainValidationError("owner_id cannot be empty")

        self.name = self.name.strip()

    def rename(self, new_name: str) -> None:
        if not new_name or not new_name.strip():
            raise DomainValidationError("Category name cannot be empty")

        self.name = new_name.strip()
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "updated_by": self.updated_by,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Category":
        return cls(
            id=uuid.UUID(data["id"]),
            name=data["name"],
            owner_id=data["owner_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            created_by=data.get("created_by"),
            updated_by=data.get("updated_by"),
        )

    def __str__(self) -> str:
        return f"Category(id={self.id}, name='{self.name}')"

    def __repr__(self) -> str:
        return f"Category(id={self.id}, name='{self.name}', owner_id={self.owner_id})"
