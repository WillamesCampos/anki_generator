"""
Exceções da camada de infraestrutura (Mongo). Antes desta sprint,
`RepositoryError` e as exceções de "não encontrado" viviam soltas dentro
de `card_repository.py`, e todo outro módulo de repositório importava
delas como se fosse um módulo compartilhado — layering estranho (infra
importando de um "irmão" de infra). Agora moram todas aqui, um único
lugar, todas descendentes de `AppError` (core/exceptions.py).
"""

from core.exceptions import AppError


class InfrastructureError(AppError):
    """Base para qualquer falha da camada de infraestrutura (Mongo, etc.)."""

    code = "infrastructure_error"


class RepositoryError(InfrastructureError):
    """Falha genérica de persistência/consulta num repositório Mongo."""

    code = "repository_error"


class CardNotFoundError(RepositoryError):
    code = "card_not_found"


class DeckNotFoundError(RepositoryError):
    code = "deck_not_found"


class CategoryNotFoundError(RepositoryError):
    code = "category_not_found"


class SessionNotFoundError(RepositoryError):
    code = "session_not_found"


class MongoNotConnectedError(InfrastructureError):
    """Uma operação foi tentada antes de `MongoDBConnectionManager.connect()`."""

    code = "mongodb_not_connected"


class MongoConfigError(InfrastructureError):
    """`MongoDBConfig` inválida (host/porta/pool size fora do esperado)."""

    code = "mongodb_invalid_config"
