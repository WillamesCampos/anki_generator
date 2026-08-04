"""
Value Objects do Domínio

Os objetos de valor representam conceitos importantes do domínio
que não têm identidade própria, mas são definidos pelo seu valor.

Características dos Value Objects:
- Imutáveis (frozen=True)
- Sem identidade (comparados por valor)
- Reutilizáveis
- Validados na criação
"""

from .word import Word
from .translation import Translation
from .example import Example
from .audio_path import AudioPath

__all__ = [
    'Word',
    'Translation', 
    'Example',
    'AudioPath'
]
