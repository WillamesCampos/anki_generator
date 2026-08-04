"""
Objeto de Valor Example - Representa um exemplo de uso da palavra

Características:
- Contém frase original em inglês
- Contém tradução da frase em português
- Ambos são validados e normalizados
- Imutável
"""

from dataclasses import dataclass
import re
from typing import Optional


@dataclass(frozen=True)
class Example:
    """
    Objeto de valor que representa um exemplo de uso da palavra.
    
    Características:
    - Imutável (frozen=True)
    - Contém frase original e tradução
    - Validado na criação
    """
    
    original: str
    translated: str
    
    def __post_init__(self):
        """
        Valida e normaliza o exemplo após a criação.
        """
        if not self.original or not self.original.strip():
            raise ValueError("Original example cannot be empty")
        
        if not self.translated or not self.translated.strip():
            raise ValueError("Translated example cannot be empty")
        
        # Normaliza as frases
        original_normalized = self.original.strip()
        translated_normalized = self.translated.strip()
        
        # Remove espaços múltiplos
        original_normalized = re.sub(r'\s+', ' ', original_normalized)
        translated_normalized = re.sub(r'\s+', ' ', translated_normalized)
        
        # Valida comprimento mínimo
        if len(original_normalized) < 10:
            raise ValueError("Original example must have at least 10 characters")
        
        if len(translated_normalized) < 10:
            raise ValueError("Translated example must have at least 10 characters")
        
        # Define os valores normalizados
        object.__setattr__(self, 'original', original_normalized)
        object.__setattr__(self, 'translated', translated_normalized)
    
    @property
    def original_normalized(self) -> str:
        """
        Retorna a versão normalizada da frase original.
        """
        return self.original.lower().strip()
    
    @property
    def translated_normalized(self) -> str:
        """
        Retorna a versão normalizada da tradução.
        """
        return self.translated.lower().strip()
    
    @property
    def word_count_original(self) -> int:
        """
        Retorna o número de palavras na frase original.
        """
        return len(self.original.split())
    
    @property
    def word_count_translated(self) -> int:
        """
        Retorna o número de palavras na tradução.
        """
        return len(self.translated.split())
    
    @property
    def length_original(self) -> int:
        """
        Retorna o comprimento da frase original.
        """
        return len(self.original)
    
    @property
    def length_translated(self) -> int:
        """
        Retorna o comprimento da tradução.
        """
        return len(self.translated)
    
    def contains_word(self, word: str) -> bool:
        """
        Verifica se a frase original contém a palavra especificada.
        
        Args:
            word: Palavra a ser pesquisada
            
        Returns:
            True se a frase contém a palavra
        """
        return word.lower() in self.original_normalized
    
    def highlight_word(self, word: str, highlight_start: str = "**", highlight_end: str = "**") -> str:
        """
        Destaca a palavra na frase original.
        
        Args:
            word: Palavra a ser destacada
            highlight_start: Marcador de início
            highlight_end: Marcador de fim
            
        Returns:
            Frase com a palavra destacada
        """
        import re
        
        # Regex para encontrar a palavra (case insensitive)
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        
        def replace_word(match):
            return f"{highlight_start}{match.group()}{highlight_end}"
        
        return pattern.sub(replace_word, self.original)
    
    def to_dict(self) -> dict:
        """
        Converte para dicionário para serialização.
        """
        return {
            "original": self.original,
            "translated": self.translated,
            "original_normalized": self.original_normalized,
            "translated_normalized": self.translated_normalized,
            "word_count_original": self.word_count_original,
            "word_count_translated": self.word_count_translated,
            "length_original": self.length_original,
            "length_translated": self.length_translated
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Example':
        """
        Cria um Example a partir de um dicionário.
        """
        return cls(
            original=data["original"],
            translated=data["translated"]
        )
    
    def __str__(self) -> str:
        return f"Original: {self.original} | Translated: {self.translated}"
    
    def __repr__(self) -> str:
        return f"Example(original='{self.original[:30]}...', translated='{self.translated[:30]}...')"
    
    def __eq__(self, other) -> bool:
        """
        Comparação baseada nos valores normalizados.
        """
        if not isinstance(other, Example):
            return False
        return (
            self.original_normalized == other.original_normalized and
            self.translated_normalized == other.translated_normalized
        )
    
    def __hash__(self) -> int:
        """
        Hash baseado nos valores normalizados.
        """
        return hash((self.original_normalized, self.translated_normalized))
