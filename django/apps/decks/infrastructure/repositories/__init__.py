"""
Implementações dos Repositórios

Este módulo contém as implementações concretas dos repositórios usando MongoDB.
Cada repositório implementa sua respectiva interface do domínio.

Implementações disponíveis:
- CardRepository: Implementação MongoDB do ICardRepository
- DeckRepository: Implementação MongoDB do IDeckRepository
- GenerationSessionRepository: Implementação MongoDB do IGenerationSessionRepository
"""

from .card_repository import CardRepository
from .deck_repository import DeckRepository
from .category_repository import CategoryRepository
from .card_review_repository import CardReviewRepository
from .generation_session_repository import GenerationSessionRepository
from ..exceptions import (
    CardNotFoundError,
    CategoryNotFoundError,
    DeckNotFoundError,
    RepositoryError,
    SessionNotFoundError,
)

__all__ = [
    "CardRepository",
    "DeckRepository",
    "CategoryRepository",
    "CardReviewRepository",
    "GenerationSessionRepository",
    "RepositoryError",
    "CardNotFoundError",
    "DeckNotFoundError",
    "CategoryNotFoundError",
    "SessionNotFoundError",
]
