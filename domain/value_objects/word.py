"""
Objeto de Valor Word - Representa uma palavra em inglês

Objetos de Valor são diferentes de Entidades:
- Não têm identidade (são definidos pelo seu valor)
- São imutáveis (não podem ser alterados)
- São reutilizáveis em diferentes contextos
- Têm validações específicas

No caso de Word:
- Deve ser uma string não vazia
- Deve conter apenas letras, espaços e hífens
- É normalizada (trim, lowercase para comparações)
"""

from dataclasses import dataclass
import re
from typing import Optional


@dataclass(frozen=True)  # frozen=True torna o objeto imutável
class Word:
    """
    Objeto de valor que representa uma palavra em inglês.
    
    Características:
    - Imutável (frozen=True)
    - Validado na criação
    - Normalizado para comparações
    """
    
    value: str
    
    def __post_init__(self):
        """
        Valida e normaliza a palavra após a criação.
        Como o objeto é frozen, usamos object.__setattr__ para modificar.
        """
        if not self.value or not self.value.strip():
            raise ValueError("Word cannot be empty")
        
        # Remove espaços extras e normaliza
        normalized_value = self.value.strip()
        
        # Valida se contém apenas letras, espaços e hífens
        if not re.match(r'^[a-zA-Z\s\-]+$', normalized_value):
            raise ValueError("Word can only contain letters, spaces and hyphens")
        
        # Remove espaços múltiplos
        normalized_value = re.sub(r'\s+', ' ', normalized_value)
        
        # Define o valor normalizado
        object.__setattr__(self, 'value', normalized_value)
    
    @property
    def normalized(self) -> str:
        """
        Retorna a versão normalizada da palavra (lowercase, sem espaços extras).
        """
        return self.value.lower().strip()
    
    @property
    def length(self) -> int:
        """
        Retorna o comprimento da palavra.
        """
        return len(self.value)
    
    @property
    def word_count(self) -> int:
        """
        Retorna o número de palavras (para frases).
        """
        return len(self.value.split())
    
    def is_single_word(self) -> bool:
        """
        Verifica se é uma única palavra (não uma frase).
        """
        return self.word_count == 1
    
    def is_phrase(self) -> bool:
        """
        Verifica se é uma frase (múltiplas palavras).
        """
        return self.word_count > 1
    
    def starts_with_vowel(self) -> bool:
        """
        Verifica se a palavra começa com vogal.
        Útil para regras gramaticais (a/an).
        """
        if not self.is_single_word():
            return False
        
        first_letter = self.value.lower()[0]
        return first_letter in 'aeiou'
    
    def to_dict(self) -> dict:
        """
        Converte para dicionário para serialização.
        """
        return {
            "value": self.value,
            "normalized": self.normalized,
            "length": self.length,
            "word_count": self.word_count
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Word':
        """
        Cria um Word a partir de um dicionário.
        """
        return cls(value=data["value"])
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"Word('{self.value}')"
    
    def __eq__(self, other) -> bool:
        """
        Comparação baseada no valor normalizado.
        """
        if not isinstance(other, Word):
            return False
        return self.normalized == other.normalized
    
    def __hash__(self) -> int:
        """
        Hash baseado no valor normalizado.
        """
        return hash(self.normalized)
