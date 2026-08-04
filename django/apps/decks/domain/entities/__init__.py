"""
Entidades do Domínio

As entidades são objetos que têm identidade única e ciclo de vida.
Elas representam os conceitos centrais do domínio e contêm as regras de negócio.

Características das Entidades:
- Identidade única (ID)
- Mutáveis (podem ser alteradas)
- Invariantes (sempre em estado válido)
- Comportamentos específicos do domínio
"""

from .card import Card
from .deck import Deck
from .generation_session import GenerationSession, GenerationStatus

__all__ = [
    'Card',
    'Deck', 
    'GenerationSession',
    'GenerationStatus'
]
