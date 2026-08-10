"""
Exceção base do projeto. Toda exceção customizada (de qualquer app) DEVE
herdar de `AppError`, direta ou indiretamente, em vez de levantar
`ValueError`/`RuntimeError`/`Exception` puros.

Isso não é só estilo: qualquer camada que precise reagir a "um erro
nosso" (um exception handler do DRF, um log estruturado, um teste) pode
fazer `except AppError` uma vez só, em vez de manter uma lista de tipos
soltos espalhada pelo projeto.

`AppError` é abstrata — Python levanta `TypeError` se alguém tentar
instanciá-la diretamente, porque toda subclasse concreta é obrigada a
implementar `code`: um identificador curto e estável (ex.:
`"card_not_found"`), pensado para ser consumido por quem lida com o erro
sem precisar de uma cadeia de `isinstance`.

Este módulo não importa nada do Django de propósito — é puro Python
(`abc` + `Exception`), então tanto a camada de domínio (que não deve
depender de nada externo) quanto a de infraestrutura podem herdar dele
sem ganhar uma dependência real do framework.
"""

from abc import ABC, abstractmethod


class AppError(Exception, ABC):
    def __init__(self, *args, **kwargs):
        # `ABC` sozinho não bloqueia instanciação aqui: `BaseException.__new__`
        # é implementado em C e não passa pela checagem de `__abstractmethods__`
        # que `object.__new__` faz normalmente — é um gotcha conhecido de
        # combinar `Exception` com `ABC`. Sem este guard manual,
        # `AppError("x")` seria instanciável mesmo com `code` abstrato.
        if type(self) is AppError:
            raise TypeError("AppError é abstrata — levante uma subclasse concreta.")
        super().__init__(*args, **kwargs)

    @property
    @abstractmethod
    def code(self) -> str:
        raise NotImplementedError
