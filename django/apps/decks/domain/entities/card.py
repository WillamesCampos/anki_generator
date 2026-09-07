"""
Entidade Card - Representa um card individual do Anki

Esta entidade é o coração do sistema. Cada card representa uma palavra/frase
que será estudada no Anki, com suas respectivas traduções e exemplos.

Características da entidade Card:
- Tem identidade única (id)
- É mutável (pode ser editada)
- Contém regras de negócio (validações)
- É independente de detalhes técnicos (banco, API, etc.)
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List
from dataclasses import dataclass, field

from ..value_objects.word import Word
from ..value_objects.translation import Translation
from ..value_objects.audio_path import AudioPath
from ..exceptions import DomainValidationError


@dataclass
class Card:
    """
    Entidade Card representa um card individual do Anki.

    Atributos:
    - front: conteúdo principal da front do card
    - back: conteúdo principal do back do card
    - front_description: descrição/contexto exibido na front
    - back_description: descrição/contexto exibido no back
    - owner_id: dono do card (isolamento multi-tenant — ver D1 em
      openspec/changes/sprint-2-decks-cards/design.md)
    - id: Identificador único (UUID)
    - audio_path: Caminho para arquivo de áudio (opcional)
    - context: Contexto que gerou este card
    - deck_id: ID do deck ao qual pertence
    - tags: tags livres para categorização/índice (ver PRD Sprint 2, 2.4)
    - stability/difficulty/due_at/fsrs_state/fsrs_step: campos de agendamento
      FSRS (ver D4 em design.md) — nunca calculados aqui, só persistidos;
      quem calcula é `domain/services/scheduling_service.py`
    - created_at: Data de criação
    - updated_at: Data da última atualização
    """

    # Objetos de valor que compõem o card (obrigatórios)
    front: Word
    back: Translation
    front_description: str
    back_description: str
    owner_id: str

    # Identidade única da entidade
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    # Campos opcionais
    audio_path: Optional[AudioPath] = None

    # Metadados
    context: str = ""
    deck_id: Optional[uuid.UUID] = None
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Agendamento de repetição espaçada (FSRS). fsrs_state usa os mesmos
    # valores do enum `fsrs.State` (1=Learning, 2=Review, 3=Relearning) sem
    # importar o pacote aqui, para o domínio não depender do algoritmo escolhido.
    fsrs_state: int = 1
    fsrs_step: Optional[int] = 0
    stability: Optional[float] = None
    difficulty: Optional[float] = None
    due_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_reviewed_at: Optional[datetime] = None

    # Auditoria (Sprint 5) — quem criou/alterou por último, preenchido pelo
    # serializer a partir da request autenticada, nunca aceito do cliente.
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    # Ciclo de vida (Sprint 6) — soft delete via timestamp, mesma
    # semântica do Deck (ver deleted_at em Deck).
    deleted_at: Optional[datetime] = None

    def __post_init__(self):
        """
        Validações que são executadas após a criação do objeto.
        Em DDD, as entidades devem sempre estar em estado válido.
        """
        self._validate_card()

    def _validate_card(self) -> None:
        """
        Valida se o card está em estado válido.

        Regras de negócio:
        1. Frente não pode estar vazia
        2. Verso não pode estar vazio
        3. As descrições devem ter pelo menos 10 caracteres
        4. Context não pode ser None (pode ser string vazia)
        5. owner_id é obrigatório (isolamento multi-tenant)
        """
        if not self.front or not self.front.value.strip():
            raise DomainValidationError("Front cannot be empty")

        if not self.back or not self.back.value.strip():
            raise DomainValidationError("Back cannot be empty")

        self.front_description = " ".join(self.front_description.split())
        self.back_description = " ".join(self.back_description.split())
        if len(self.front_description) < 10:
            raise DomainValidationError(
                "front_description must have at least 10 characters"
            )
        if len(self.back_description) < 10:
            raise DomainValidationError(
                "back_description must have at least 10 characters"
            )

        if self.context is None:
            self.context = ""

        if not self.owner_id or not str(self.owner_id).strip():
            raise DomainValidationError("owner_id cannot be empty")

    def add_audio(self, audio_path: AudioPath) -> None:
        """
        Adiciona áudio ao card.

        Regra de negócio: Um card pode ter apenas um áudio.
        Se já existir, substitui o anterior.
        """
        self.audio_path = audio_path
        self.updated_at = datetime.now(timezone.utc)

    def update_back(self, new_back: Translation) -> None:
        """
        Atualiza o back do card.

        Regra de negócio: O back deve ser diferente do atual.
        """
        if new_back.value.strip() == self.back.value.strip():
            raise DomainValidationError("New back must be different from current")

        self.back = new_back
        self.updated_at = datetime.now(timezone.utc)

    def update_descriptions(
        self, front_description: str, back_description: str
    ) -> None:
        """
        Atualiza as descrições da front e do back.

        Regra de negócio: cada descrição deve ter pelo menos 10 caracteres.
        """
        front_description = " ".join(front_description.split())
        back_description = " ".join(back_description.split())
        if len(front_description) < 10 or len(back_description) < 10:
            raise DomainValidationError(
                "Card descriptions must have at least 10 characters"
            )

        self.front_description = front_description
        self.back_description = back_description
        self.updated_at = datetime.now(timezone.utc)

    def assign_to_deck(self, deck_id: uuid.UUID) -> None:
        """
        Associa o card a um deck específico.

        Regra de negócio: Um card pode pertencer a apenas um deck.
        """
        self.deck_id = deck_id
        self.updated_at = datetime.now(timezone.utc)

    def soft_delete(self) -> None:
        """Marca o card como excluído (soft delete) — não remove fisicamente."""
        self.deleted_at = datetime.now(timezone.utc)
        self.updated_at = self.deleted_at

    def is_similar_to(self, other: "Card", similarity_threshold: float = 0.8) -> bool:
        """
        Verifica se este card é similar a outro card.

        Usado para detecção de duplicatas.
        Por enquanto, compara apenas as palavras, mas pode ser expandido
        para usar algoritmos de similaridade mais sofisticados.

        Args:
            other: Outro card para comparação
            similarity_threshold: Limiar de similaridade (0.0 a 1.0)

        Returns:
            True se os cards forem considerados similares
        """
        if not isinstance(other, Card):
            return False

        # Comparação simples por enquanto
        # TODO: Implementar algoritmo de similaridade mais sofisticado
        word_similarity = (
            self.front.value.lower().strip() == other.front.value.lower().strip()
        )
        translation_similarity = (
            self.back.value.lower().strip() == other.back.value.lower().strip()
        )

        return word_similarity and translation_similarity

    def to_dict(self) -> dict:
        """
        Converte o card para dicionário.

        Útil para serialização e persistência.
        """
        return {
            "id": str(self.id),
            "front": self.front.to_dict(),
            "back": self.back.to_dict(),
            "front_description": self.front_description,
            "back_description": self.back_description,
            "owner_id": self.owner_id,
            "audio_path": self.audio_path.to_dict() if self.audio_path else None,
            "context": self.context,
            "deck_id": str(self.deck_id) if self.deck_id else None,
            "tags": list(self.tags),
            "fsrs_state": self.fsrs_state,
            "fsrs_step": self.fsrs_step,
            "stability": self.stability,
            "difficulty": self.difficulty,
            "due_at": self.due_at.isoformat(),
            "last_reviewed_at": (
                self.last_reviewed_at.isoformat() if self.last_reviewed_at else None
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Card":
        """
        Cria um card a partir de um dicionário.

        Útil para desserialização e recuperação do banco.
        """
        from ..value_objects.word import Word
        from ..value_objects.translation import Translation
        from ..value_objects.audio_path import AudioPath

        return cls(
            id=uuid.UUID(data["id"]),
            front=Word.from_dict(data["front"]),
            back=Translation.from_dict(data["back"]),
            front_description=data["front_description"],
            back_description=data["back_description"],
            owner_id=data["owner_id"],
            audio_path=(
                AudioPath.from_dict(data["audio_path"])
                if data.get("audio_path")
                else None
            ),
            context=data.get("context", ""),
            tags=list(data.get("tags", [])),
            fsrs_state=data.get("fsrs_state", 1),
            fsrs_step=data.get("fsrs_step", 0),
            stability=data.get("stability"),
            difficulty=data.get("difficulty"),
            due_at=(
                datetime.fromisoformat(data["due_at"])
                if data.get("due_at")
                else datetime.now(timezone.utc)
            ),
            last_reviewed_at=(
                datetime.fromisoformat(data["last_reviewed_at"])
                if data.get("last_reviewed_at")
                else None
            ),
            deck_id=uuid.UUID(data["deck_id"]) if data.get("deck_id") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            created_by=data.get("created_by"),
            updated_by=data.get("updated_by"),
            deleted_at=(
                datetime.fromisoformat(data["deleted_at"])
                if data.get("deleted_at")
                else None
            ),
        )

    def __str__(self) -> str:
        return (
            f"Card(id={self.id}, front='{self.front.value}', back='{self.back.value}')"
        )

    def __repr__(self) -> str:
        return f"Card(id={self.id}, front='{self.front.value}', back='{self.back.value}', deck_id={self.deck_id})"
