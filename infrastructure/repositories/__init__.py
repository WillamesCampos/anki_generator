"""
Implementações dos Repositórios

Este módulo contém as implementações concretas dos repositórios usando MongoDB.
Cada repositório implementa sua respectiva interface do domínio.

Implementações disponíveis:
- CardRepository: Implementação MongoDB do ICardRepository
- DeckRepository: Implementação MongoDB do IDeckRepository  
- GenerationSessionRepository: Implementação MongoDB do IGenerationSessionRepository
"""

from .card_repository import CardRepository, RepositoryError, CardNotFoundError
from .deck_repository import DeckRepository, DeckNotFoundError
from .generation_session_repository import GenerationSessionRepository, SessionNotFoundError

__all__ = [
    'CardRepository',
    'DeckRepository', 
    'GenerationSessionRepository',
    'RepositoryError',
    'CardNotFoundError',
    'DeckNotFoundError',
    'SessionNotFoundError'
]
