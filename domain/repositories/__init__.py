"""
Interfaces dos Repositórios

Os repositórios definem contratos para acesso a dados, seguindo o princípio
da inversão de dependência. O domínio define as interfaces e a infraestrutura
implementa essas interfaces.

Características dos Repositórios:
- Abstrações puras (sem implementação)
- Contratos bem definidos
- Independentes de tecnologia
- Focam nas operações de negócio
"""

from .icard_repository import ICardRepository
from .ideck_repository import IDeckRepository
from .igeneration_session_repository import IGenerationSessionRepository

__all__ = [
    'ICardRepository',
    'IDeckRepository',
    'IGenerationSessionRepository'
]
