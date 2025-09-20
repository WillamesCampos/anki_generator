"""
Objeto de Valor Translation - Representa uma tradução em português

Características:
- Imutável
- Validado (não pode ser vazia)
- Normalizado para comparações
- Suporta múltiplas traduções separadas por vírgula
"""

from dataclasses import dataclass
import re
from typing import List


@dataclass(frozen=True)
class Translation:
    """
    Objeto de valor que representa uma tradução em português.
    
    Características:
    - Imutável (frozen=True)
    - Validado na criação
    - Suporta múltiplas traduções
    """
    
    value: str
    
    def __post_init__(self):
        """
        Valida e normaliza a tradução após a criação.
        """
        if not self.value or not self.value.strip():
            raise ValueError("Translation cannot be empty")
        
        # Remove espaços extras e normaliza
        normalized_value = self.value.strip()
        
        # Remove espaços múltiplos
        normalized_value = re.sub(r'\s+', ' ', normalized_value)
        
        # Define o valor normalizado
        object.__setattr__(self, 'value', normalized_value)
    
    @property
    def normalized(self) -> str:
        """
        Retorna a versão normalizada da tradução (lowercase, sem espaços extras).
        """
        return self.value.lower().strip()
    
    @property
    def translations_list(self) -> List[str]:
        """
        Retorna uma lista das traduções individuais.
        Separa por vírgula e remove espaços extras.
        """
        return [t.strip() for t in self.value.split(',') if t.strip()]
    
    @property
    def primary_translation(self) -> str:
        """
        Retorna a primeira tradução (principal).
        """
        translations = self.translations_list
        return translations[0] if translations else self.value
    
    @property
    def alternative_translations(self) -> List[str]:
        """
        Retorna as traduções alternativas (excluindo a principal).
        """
        translations = self.translations_list
        return translations[1:] if len(translations) > 1 else []
    
    @property
    def has_alternatives(self) -> bool:
        """
        Verifica se há traduções alternativas.
        """
        return len(self.translations_list) > 1
    
    @property
    def translation_count(self) -> int:
        """
        Retorna o número de traduções disponíveis.
        """
        return len(self.translations_list)
    
    def contains_translation(self, search_term: str) -> bool:
        """
        Verifica se alguma das traduções contém o termo pesquisado.
        
        Args:
            search_term: Termo a ser pesquisado
            
        Returns:
            True se alguma tradução contém o termo
        """
        search_lower = search_term.lower().strip()
        return any(
            search_lower in translation.lower()
            for translation in self.translations_list
        )
    
    def to_dict(self) -> dict:
        """
        Converte para dicionário para serialização.
        """
        return {
            "value": self.value,
            "normalized": self.normalized,
            "translations_list": self.translations_list,
            "primary_translation": self.primary_translation,
            "alternative_translations": self.alternative_translations,
            "translation_count": self.translation_count
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Translation':
        """
        Cria um Translation a partir de um dicionário.
        """
        return cls(value=data["value"])
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"Translation('{self.value}')"
    
    def __eq__(self, other) -> bool:
        """
        Comparação baseada no valor normalizado.
        """
        if not isinstance(other, Translation):
            return False
        return self.normalized == other.normalized
    
    def __hash__(self) -> int:
        """
        Hash baseado no valor normalizado.
        """
        return hash(self.normalized)
