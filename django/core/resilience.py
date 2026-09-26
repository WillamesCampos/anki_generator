"""
Retry exponencial + circuit breaker para chamadas Django -> microsserviço
(Sprint 11, D3; critério de aceite 9). Reutilizável: qualquer call-site
(exportação Anki, PDF, e as integrações das Sprints 13/14) passa a operação
de UMA tentativa a `call_with_resilience`.

Como as duas camadas se compõem (`pybreaker` por FORA, `tenacity` por DENTRO):
o breaker enxerga a operação inteira — todas as tentativas — como um único
sucesso ou uma única falha. Se contasse cada tentativa, uma chamada com 2
tentativas já consumiria 2 do `fail_max`, abrindo o breaker cedo demais.

Classificação (quem retenta e quem conta pro breaker):
  - transitória = timeout, erro de conexão ou resposta 5xx -> retentada e, se
    esgotar as tentativas, conta como falha pro breaker;
  - 4xx = erro do chamador (payload ruim, JWT inválido): devolvida na hora,
    sem retry e sem tocar no breaker — o serviço está saudável, retentar não
    muda o resultado.

O estado do breaker fica no Redis (`CircuitRedisStorage`), não na memória do
processo: o worker Celery é prefork e o tráfego é esporádico, então contadores
por processo dificilmente chegariam a `fail_max` em algum deles. Um breaker
por serviço-alvo (namespace). Se o Redis estiver fora, degrada para um breaker
em memória (sem estado compartilhado) em vez de derrubar a chamada.
"""

import logging
from functools import lru_cache
from typing import Callable, Optional

import pybreaker
import redis
import requests
import tenacity
from django.conf import settings

from .exceptions import AppError

logger = logging.getLogger(__name__)


class TransientServiceError(AppError):
    """O serviço respondeu 5xx em todas as tentativas (carrega a última resposta)."""

    code = "service_unavailable"

    def __init__(self, message: str, response: Optional[requests.Response] = None):
        super().__init__(message)
        self.response = response


TRANSIENT_EXCEPTIONS = (
    requests.Timeout,
    requests.ConnectionError,
    TransientServiceError,
)


@lru_cache(maxsize=None)
def get_redis(url: str) -> redis.Redis:
    # SEM `decode_responses`: o `pybreaker` decodifica os bytes por conta própria.
    return redis.Redis.from_url(url, socket_connect_timeout=1, socket_timeout=1)


def _breaker_for(service: str) -> pybreaker.CircuitBreaker:
    storage = None
    try:
        storage = pybreaker.CircuitRedisStorage(
            pybreaker.STATE_CLOSED,
            get_redis(settings.REDIS_URL),
            namespace=f"breaker:{service}",
        )
    except redis.RedisError:
        # o construtor já fala com o Redis; fora do ar, sem estado compartilhado
        logger.warning(
            "Redis indisponível: circuit breaker de %s só em memória", service
        )

    return pybreaker.CircuitBreaker(
        fail_max=settings.SERVICE_BREAKER_FAIL_MAX,
        reset_timeout=settings.SERVICE_BREAKER_RESET_TIMEOUT,
        state_storage=storage,
        name=service,
        # a chamada que abre o breaker relata a causa real, não um erro genérico
        throw_new_error_on_trip=False,
    )


def call_with_resilience(
    service: str,
    operation: Callable[[], requests.Response],
    *,
    attempts: Optional[int] = None,
) -> requests.Response:
    """
    Executa `operation` (UMA tentativa HTTP que devolve `requests.Response`)
    com retry exponencial dentro de um circuit breaker do `service`.

    Raises:
        pybreaker.CircuitBreakerError: breaker aberto — nenhuma requisição foi feita.
        TransientServiceError: 5xx em todas as tentativas.
        requests.Timeout / requests.ConnectionError: idem, para falhas de rede.
    """

    def attempt() -> requests.Response:
        response = operation()
        if response.status_code >= 500:
            raise TransientServiceError(
                f"{service} responded {response.status_code}", response
            )
        return response

    retrying = tenacity.Retrying(
        stop=tenacity.stop_after_attempt(attempts or settings.SERVICE_RETRY_ATTEMPTS),
        wait=tenacity.wait_exponential_jitter(
            initial=settings.SERVICE_RETRY_WAIT_INITIAL,
            max=settings.SERVICE_RETRY_WAIT_MAX,
            jitter=settings.SERVICE_RETRY_JITTER,
        ),
        retry=tenacity.retry_if_exception_type(TRANSIENT_EXCEPTIONS),
        reraise=True,
    )
    return _breaker_for(service).call(retrying, attempt)
