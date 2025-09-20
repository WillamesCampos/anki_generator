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
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, field

from ..value_objects.word import Word
from ..value_objects.translation import Translation
from ..value_objects.example import Example
from ..value_objects.audio_path import AudioPath


@dataclass
class Card:
    """
    Entidade Card representa um card individual do Anki.
    
    Atributos:
    - id: Identificador único (UUID)
    - word: Objeto de valor Word (palavra em inglês)
    - translation: Objeto de valor Translation (tradução em português)
    - example: Objeto de valor Example (frase de exemplo)
    - audio_path: Caminho para arquivo de áudio (opcional)
    - context: Contexto que gerou este card
    - deck_id: ID do deck ao qual pertence
    - created_at: Data de criação
    - updated_at: Data da última atualização
    """
    
    # Identidade única da entidade
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    
    # Objetos de valor que compõem o card
    word: Word
    translation: Translation
    example: Example
    audio_path: Optional[AudioPath] = None
    
    # Metadados
    context: str = ""
    deck_id: Optional[uuid.UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
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
        1. Word não pode estar vazia
        2. Translation não pode estar vazia
        3. Example deve ter pelo menos 10 caracteres
        4. Context não pode ser None (pode ser string vazia)
        """
        if not self.word or not self.word.value.strip():
            raise ValueError("Word cannot be empty")
        
        if not self.translation or not self.translation.value.strip():
            raise ValueError("Translation cannot be empty")
        
        if not self.example or len(self.example.original.strip()) < 10:
            raise ValueError("Example must have at least 10 characters")
        
        if self.context is None:
            self.context = ""
    
    def add_audio(self, audio_path: AudioPath) -> None:
        """
        Adiciona áudio ao card.
        
        Regra de negócio: Um card pode ter apenas um áudio.
        Se já existir, substitui o anterior.
        """
        self.audio_path = audio_path
        self.updated_at = datetime.utcnow()
    
    def update_translation(self, new_translation: Translation) -> None:
        """
        Atualiza a tradução do card.
        
        Regra de negócio: A tradução deve ser diferente da atual.
        """
        if new_translation.value.strip() == self.translation.value.strip():
            raise ValueError("New translation must be different from current")
        
        self.translation = new_translation
        self.updated_at = datetime.utcnow()
    
    def update_example(self, new_example: Example) -> None:
        """
        Atualiza o exemplo do card.
        
        Regra de negócio: O exemplo deve ter pelo menos 10 caracteres.
        """
        if len(new_example.original.strip()) < 10:
            raise ValueError("Example must have at least 10 characters")
        
        self.example = new_example
        self.updated_at = datetime.utcnow()
    
    def assign_to_deck(self, deck_id: uuid.UUID) -> None:
        """
        Associa o card a um deck específico.
        
        Regra de negócio: Um card pode pertencer a apenas um deck.
        """
        self.deck_id = deck_id
        self.updated_at = datetime.utcnow()
    
    def is_similar_to(self, other: 'Card', similarity_threshold: float = 0.8) -> bool:
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
        word_similarity = self.word.value.lower().strip() == other.word.value.lower().strip()
        translation_similarity = self.translation.value.lower().strip() == other.translation.value.lower().strip()
        
        return word_similarity and translation_similarity
    
    def to_dict(self) -> dict:
        """
        Converte o card para dicionário.
        
        Útil para serialização e persistência.
        """
        return {
            "id": str(self.id),
            "word": self.word.to_dict(),
            "translation": self.translation.to_dict(),
            "example": self.example.to_dict(),
            "audio_path": self.audio_path.to_dict() if self.audio_path else None,
            "context": self.context,
            "deck_id": str(self.deck_id) if self.deck_id else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Card':
        """
        Cria um card a partir de um dicionário.
        
        Útil para desserialização e recuperação do banco.
        """
        from ..value_objects.word import Word
        from ..value_objects.translation import Translation
        from ..value_objects.example import Example
        from ..value_objects.audio_path import AudioPath
        
        return cls(
            id=uuid.UUID(data["id"]),
            word=Word.from_dict(data["word"]),
            translation=Translation.from_dict(data["translation"]),
            example=Example.from_dict(data["example"]),
            audio_path=AudioPath.from_dict(data["audio_path"]) if data.get("audio_path") else None,
            context=data.get("context", ""),
            deck_id=uuid.UUID(data["deck_id"]) if data.get("deck_id") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )
    
    def __str__(self) -> str:
        return f"Card(id={self.id}, word='{self.word.value}', translation='{self.translation.value}')"
    
    def __repr__(self) -> str:
        return f"Card(id={self.id}, word='{self.word.value}', translation='{self.translation.value}', deck_id={self.deck_id})"
