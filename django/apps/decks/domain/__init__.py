"""
Domínio - Camada de Regras de Negócio

Esta é a camada mais importante do DDD, onde ficam todas as regras de negócio.
Ela é independente de detalhes técnicos como banco de dados, APIs, etc.

Estrutura:
- entities/: Entidades com identidade única
- value_objects/: Objetos de valor imutáveis
- repositories/: Interfaces para acesso a dados
- services/: Serviços de domínio para regras complexas
"""

from .entities import Card, Deck, GenerationSession, GenerationStatus
from .value_objects import Word, Translation, Example, AudioPath

__all__ = [
    # Entidades
    'Card',
    'Deck',
    'GenerationSession', 
    'GenerationStatus',
    
    # Value Objects
    'Word',
    'Translation',
    'Example',
    'AudioPath'
]
