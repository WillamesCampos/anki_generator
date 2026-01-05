"""
Entidade Deck - Representa uma coleção de cards do Anki

Um Deck é uma coleção organizada de cards que serão estudados no Anki.
Cada deck tem:
- Identidade única
- Título e descrição
- Lista de cards
- Metadados (criação, atualização, etc.)
- Regras de negócio específicas
"""

import uuid
from datetime import datetime
from typing import List, Optional, Set
from dataclasses import dataclass, field

from .card import Card


@dataclass
class Deck:
    """
    Entidade Deck representa uma coleção de cards do Anki.
    
    Atributos:
    - title: Título do deck
    - id: Identificador único (UUID)
    - description: Descrição opcional do deck
    - cards: Lista de cards no deck
    - max_cards_per_generation: Máximo de cards por geração (padrão 10)
    - created_at: Data de criação
    - updated_at: Data da última atualização
    """
    
    # Propriedades básicas (obrigatórias)
    title: str
    
    # Identidade única da entidade
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    
    # Campos opcionais
    description: str = ""
    
    # Cards do deck
    cards: List[Card] = field(default_factory=list)
    
    # Configurações
    max_cards_per_generation: int = 10
    
    # Metadados
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """
        Validações que são executadas após a criação do objeto.
        """
        self._validate_deck()
    
    def _validate_deck(self) -> None:
        """
        Valida se o deck está em estado válido.
        
        Regras de negócio:
        1. Título não pode estar vazio
        2. Máximo de cards por geração deve ser entre 1 e 20
        3. Descrição pode ser vazia mas não None
        """
        if not self.title or not self.title.strip():
            raise ValueError("Deck title cannot be empty")
        
        if not (1 <= self.max_cards_per_generation <= 20):
            raise ValueError("Max cards per generation must be between 1 and 20")
        
        if self.description is None:
            self.description = ""
        
        # Normaliza o título
        self.title = self.title.strip()
    
    @property
    def card_count(self) -> int:
        """
        Retorna o número de cards no deck.
        """
        return len(self.cards)
    
    @property
    def is_empty(self) -> bool:
        """
        Verifica se o deck está vazio.
        """
        return self.card_count == 0
    
    @property
    def has_cards(self) -> bool:
        """
        Verifica se o deck tem cards.
        """
        return self.card_count > 0
    
    @property
    def unique_words(self) -> Set[str]:
        """
        Retorna um conjunto com todas as palavras únicas no deck.
        Útil para verificação de duplicatas.
        """
        return {card.word.normalized for card in self.cards}
    
    @property
    def contexts_used(self) -> Set[str]:
        """
        Retorna um conjunto com todos os contextos usados no deck.
        """
        return {card.context for card in self.cards if card.context}
    
    def add_card(self, card: Card) -> None:
        """
        Adiciona um card ao deck.
        
        Regras de negócio:
        1. Card não pode ser None
        2. Card deve ser associado ao deck
        3. Atualiza timestamp de modificação
        """
        if card is None:
            raise ValueError("Card cannot be None")
        
        # Associa o card ao deck
        card.assign_to_deck(self.id)
        
        # Adiciona o card à lista
        self.cards.append(card)
        
        # Atualiza timestamp
        self.updated_at = datetime.utcnow()
    
    def add_cards(self, cards: List[Card]) -> None:
        """
        Adiciona múltiplos cards ao deck.
        
        Args:
            cards: Lista de cards para adicionar
        """
        if not cards:
            return
        
        for card in cards:
            self.add_card(card)
    
    def remove_card(self, card_id: uuid.UUID) -> bool:
        """
        Remove um card do deck.
        
        Args:
            card_id: ID do card a ser removido
            
        Returns:
            True se o card foi removido, False se não foi encontrado
        """
        for i, card in enumerate(self.cards):
            if card.id == card_id:
                del self.cards[i]
                self.updated_at = datetime.utcnow()
                return True
        
        return False
    
    def get_card_by_id(self, card_id: uuid.UUID) -> Optional[Card]:
        """
        Busca um card pelo ID.
        
        Args:
            card_id: ID do card
            
        Returns:
            Card se encontrado, None caso contrário
        """
        for card in self.cards:
            if card.id == card_id:
                return card
        
        return None
    
    def get_cards_by_context(self, context: str) -> List[Card]:
        """
        Busca cards por contexto.
        
        Args:
            context: Contexto para buscar
            
        Returns:
            Lista de cards que usam o contexto especificado
        """
        return [card for card in self.cards if card.context == context]
    
    def has_word(self, word: str) -> bool:
        """
        Verifica se o deck já contém uma palavra específica.
        
        Args:
            word: Palavra para verificar
            
        Returns:
            True se a palavra já existe no deck
        """
        word_normalized = word.lower().strip()
        return word_normalized in self.unique_words
    
    def find_similar_card(self, word: str) -> Optional[Card]:
        """
        Busca um card similar à palavra especificada.
        
        Args:
            word: Palavra para buscar
            
        Returns:
            Card similar se encontrado, None caso contrário
        """
        word_normalized = word.lower().strip()
        
        for card in self.cards:
            if card.word.normalized == word_normalized:
                return card
        
        return None
    
    def can_add_more_cards(self, count: int = 1) -> bool:
        """
        Verifica se pode adicionar mais cards sem exceder o limite.
        
        Args:
            count: Número de cards que se deseja adicionar
            
        Returns:
            True se pode adicionar, False caso contrário
        """
        return self.card_count + count <= self.max_cards_per_generation * 10  # Limite razoável
    
    def get_generation_batches(self) -> List[List[Card]]:
        """
        Divide os cards em lotes para geração.
        
        Returns:
            Lista de lotes, cada um com até max_cards_per_generation cards
        """
        batches = []
        for i in range(0, len(self.cards), self.max_cards_per_generation):
            batch = self.cards[i:i + self.max_cards_per_generation]
            batches.append(batch)
        
        return batches
    
    def update_title(self, new_title: str) -> None:
        """
        Atualiza o título do deck.
        
        Args:
            new_title: Novo título
        """
        if not new_title or not new_title.strip():
            raise ValueError("Deck title cannot be empty")
        
        self.title = new_title.strip()
        self.updated_at = datetime.utcnow()
    
    def update_description(self, new_description: str) -> None:
        """
        Atualiza a descrição do deck.
        
        Args:
            new_description: Nova descrição
        """
        if new_description is None:
            new_description = ""
        
        self.description = new_description
        self.updated_at = datetime.utcnow()
    
    def clear_cards(self) -> None:
        """
        Remove todos os cards do deck.
        """
        self.cards.clear()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """
        Converte o deck para dicionário.
        """
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "cards": [card.to_dict() for card in self.cards],
            "max_cards_per_generation": self.max_cards_per_generation,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "card_count": self.card_count,
            "is_empty": self.is_empty
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Deck':
        """
        Cria um deck a partir de um dicionário.
        """
        deck = cls(
            id=uuid.UUID(data["id"]),
            title=data["title"],
            description=data.get("description", ""),
            max_cards_per_generation=data.get("max_cards_per_generation", 10),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )
        
        # Adiciona os cards
        cards_data = data.get("cards", [])
        for card_data in cards_data:
            card = Card.from_dict(card_data)
            deck.cards.append(card)
        
        return deck
    
    def __str__(self) -> str:
        return f"Deck(id={self.id}, title='{self.title}', cards={self.card_count})"
    
    def __repr__(self) -> str:
        return f"Deck(id={self.id}, title='{self.title}', cards={self.card_count}, created_at={self.created_at})"
