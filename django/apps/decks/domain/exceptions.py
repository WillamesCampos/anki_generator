"""
Exceções de validação de domínio. Toda violação de invariante em
entidades/objetos de valor (`Card`, `Deck`, `Category`, `CardReview`,
`Word`, `Translation`, `AudioPath`, `GenerationSession`) usa
`DomainValidationError` em vez de `ValueError` puro — quem captura sabe
que é "um erro de validação nosso" via `except DomainValidationError`
(que por sua vez é um `except AppError`, ver core/exceptions.py).
"""

from core.exceptions import AppError


class DomainValidationError(AppError):
    code = "domain_validation_error"
