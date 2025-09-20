"""
Entidade GenerationSession - Controla uma sessão de geração de cards

Uma GenerationSession representa uma sessão de geração de cards baseada em um contexto.
Ela controla:
- O contexto fornecido pelo usuário
- Os cards gerados na sessão
- O status da sessão (em andamento, concluída, etc.)
- Metadados sobre a geração
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional
from dataclasses import dataclass, field

from .card import Card


class GenerationStatus(Enum):
    """
    Status possíveis de uma sessão de geração.
    """
    PENDING = "pending"           # Sessão criada, aguardando processamento
    IN_PROGRESS = "in_progress"   # Sessão sendo processada
    COMPLETED = "completed"       # Sessão concluída com sucesso
    FAILED = "failed"            # Sessão falhou
    CANCELLED = "cancelled"       # Sessão cancelada


@dataclass
class GenerationSession:
    """
    Entidade GenerationSession controla uma sessão de geração de cards.
    
    Atributos:
    - id: Identificador único da sessão
    - context: Contexto fornecido pelo usuário
    - deck_id: ID do deck associado
    - status: Status atual da sessão
    - generated_cards: Cards gerados na sessão
    - max_cards: Máximo de cards a serem gerados
    - created_at: Data de criação
    - updated_at: Data da última atualização
    - completed_at: Data de conclusão (se aplicável)
    - error_message: Mensagem de erro (se aplicável)
    """
    
    # Identidade única da entidade
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    
    # Propriedades da sessão
    context: str
    deck_id: uuid.UUID
    
    # Status e controle
    status: GenerationStatus = GenerationStatus.PENDING
    generated_cards: List[Card] = field(default_factory=list)
    max_cards: int = 10
    
    # Metadados
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """
        Validações que são executadas após a criação do objeto.
        """
        self._validate_session()
    
    def _validate_session(self) -> None:
        """
        Valida se a sessão está em estado válido.
        
        Regras de negócio:
        1. Contexto não pode estar vazio
        2. Máximo de cards deve ser entre 1 e 20
        3. Deck ID não pode ser None
        """
        if not self.context or not self.context.strip():
            raise ValueError("Context cannot be empty")
        
        if not (1 <= self.max_cards <= 20):
            raise ValueError("Max cards must be between 1 and 20")
        
        if self.deck_id is None:
            raise ValueError("Deck ID cannot be None")
        
        # Normaliza o contexto
        self.context = self.context.strip()
    
    @property
    def cards_generated_count(self) -> int:
        """
        Retorna o número de cards gerados na sessão.
        """
        return len(self.generated_cards)
    
    @property
    def is_pending(self) -> bool:
        """
        Verifica se a sessão está pendente.
        """
        return self.status == GenerationStatus.PENDING
    
    @property
    def is_in_progress(self) -> bool:
        """
        Verifica se a sessão está em andamento.
        """
        return self.status == GenerationStatus.IN_PROGRESS
    
    @property
    def is_completed(self) -> bool:
        """
        Verifica se a sessão foi concluída.
        """
        return self.status == GenerationStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """
        Verifica se a sessão falhou.
        """
        return self.status == GenerationStatus.FAILED
    
    @property
    def is_cancelled(self) -> bool:
        """
        Verifica se a sessão foi cancelada.
        """
        return self.status == GenerationStatus.CANCELLED
    
    @property
    def is_finished(self) -> bool:
        """
        Verifica se a sessão foi finalizada (concluída, falhou ou cancelada).
        """
        return self.status in [GenerationStatus.COMPLETED, GenerationStatus.FAILED, GenerationStatus.CANCELLED]
    
    @property
    def can_add_cards(self) -> bool:
        """
        Verifica se ainda pode adicionar cards à sessão.
        """
        return (
            self.status in [GenerationStatus.PENDING, GenerationStatus.IN_PROGRESS] and
            self.cards_generated_count < self.max_cards
        )
    
    def start_generation(self) -> None:
        """
        Inicia a geração de cards.
        
        Regras de negócio:
        1. Só pode iniciar se estiver pendente
        2. Atualiza status para IN_PROGRESS
        """
        if not self.is_pending:
            raise ValueError(f"Cannot start generation. Current status: {self.status.value}")
        
        self.status = GenerationStatus.IN_PROGRESS
        self.updated_at = datetime.utcnow()
    
    def add_generated_card(self, card: Card) -> None:
        """
        Adiciona um card gerado à sessão.
        
        Regras de negócio:
        1. Só pode adicionar se a sessão permitir
        2. Card deve ser associado ao deck da sessão
        3. Não pode exceder o máximo de cards
        """
        if not self.can_add_cards:
            raise ValueError(f"Cannot add card. Status: {self.status.value}, Cards: {self.cards_generated_count}/{self.max_cards}")
        
        if card is None:
            raise ValueError("Card cannot be None")
        
        # Associa o card ao deck da sessão
        card.assign_to_deck(self.deck_id)
        
        # Adiciona o card
        self.generated_cards.append(card)
        
        # Atualiza timestamp
        self.updated_at = datetime.utcnow()
    
    def complete_generation(self) -> None:
        """
        Marca a sessão como concluída.
        
        Regras de negócio:
        1. Só pode concluir se estiver em andamento
        2. Deve ter pelo menos um card gerado
        3. Atualiza timestamp de conclusão
        """
        if not self.is_in_progress:
            raise ValueError(f"Cannot complete generation. Current status: {self.status.value}")
        
        if self.cards_generated_count == 0:
            raise ValueError("Cannot complete generation without any cards")
        
        self.status = GenerationStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def fail_generation(self, error_message: str) -> None:
        """
        Marca a sessão como falhada.
        
        Args:
            error_message: Mensagem descritiva do erro
        """
        if self.is_finished:
            raise ValueError(f"Cannot fail generation. Current status: {self.status.value}")
        
        self.status = GenerationStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def cancel_generation(self) -> None:
        """
        Cancela a sessão de geração.
        """
        if self.is_finished:
            raise ValueError(f"Cannot cancel generation. Current status: {self.status.value}")
        
        self.status = GenerationStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def get_cards_by_word(self, word: str) -> List[Card]:
        """
        Busca cards gerados por palavra.
        
        Args:
            word: Palavra para buscar
            
        Returns:
            Lista de cards que contêm a palavra
        """
        word_normalized = word.lower().strip()
        return [
            card for card in self.generated_cards
            if card.word.normalized == word_normalized
        ]
    
    def has_duplicate_word(self, word: str) -> bool:
        """
        Verifica se já existe um card com a palavra especificada.
        
        Args:
            word: Palavra para verificar
            
        Returns:
            True se já existe um card com essa palavra
        """
        return len(self.get_cards_by_word(word)) > 0
    
    def get_unique_words(self) -> List[str]:
        """
        Retorna lista de palavras únicas geradas na sessão.
        """
        return list(set(card.word.normalized for card in self.generated_cards))
    
    def to_dict(self) -> dict:
        """
        Converte a sessão para dicionário.
        """
        return {
            "id": str(self.id),
            "context": self.context,
            "deck_id": str(self.deck_id),
            "status": self.status.value,
            "generated_cards": [card.to_dict() for card in self.generated_cards],
            "max_cards": self.max_cards,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "cards_generated_count": self.cards_generated_count,
            "is_finished": self.is_finished
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'GenerationSession':
        """
        Cria uma sessão a partir de um dicionário.
        """
        session = cls(
            id=uuid.UUID(data["id"]),
            context=data["context"],
            deck_id=uuid.UUID(data["deck_id"]),
            status=GenerationStatus(data["status"]),
            max_cards=data.get("max_cards", 10),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            error_message=data.get("error_message")
        )
        
        # Adiciona os cards gerados
        cards_data = data.get("generated_cards", [])
        for card_data in cards_data:
            card = Card.from_dict(card_data)
            session.generated_cards.append(card)
        
        return session
    
    def __str__(self) -> str:
        return f"GenerationSession(id={self.id}, status={self.status.value}, cards={self.cards_generated_count})"
    
    def __repr__(self) -> str:
        return f"GenerationSession(id={self.id}, status={self.status.value}, cards={self.cards_generated_count}, context='{self.context[:30]}...')"
