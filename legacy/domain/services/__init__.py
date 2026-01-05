"""
Serviços de Domínio

Os serviços de domínio contêm lógica de negócio que não pertence naturalmente
a uma entidade específica. Eles encapsulam operações complexas e regras
de negócio que envolvem múltiplas entidades ou conceitos.

Características dos Serviços de Domínio:
- Lógica de negócio pura (sem dependências externas)
- Operações que não pertencem a uma entidade específica
- Comportamentos complexos e regras de negócio
- Reutilizáveis em diferentes contextos
"""

from .duplicate_detection_service import DuplicateDetectionService
from .card_quality_service import CardQualityService, QualityReport, QualityLevel

__all__ = [
    'DuplicateDetectionService',
    'CardQualityService',
    'QualityReport',
    'QualityLevel'
]
