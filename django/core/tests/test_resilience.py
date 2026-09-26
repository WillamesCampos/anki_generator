"""Retry exponencial + circuit breaker (Sprint 11, D3; critério de aceite 9).

Regras testadas: só falha transitória (timeout, conexão, 5xx) é retentada; 4xx
falha na hora e não conta pro breaker; o breaker vê a operação inteira (todas
as tentativas) como UMA falha; o estado vive no Redis, então vale entre
processos; um breaker por serviço."""

import time
from unittest.mock import Mock

import pybreaker
import pytest
import requests
from django.conf import settings as django_settings

from core.resilience import TransientServiceError, call_with_resilience


def response(status=200):
    r = requests.Response()
    r.status_code = status
    r._content = b"body"
    return r


class Operation:
    """Operação de uma tentativa que segue um roteiro de resultados/erros."""

    def __init__(self, *script):
        self.script = list(script)
        self.calls = 0

    def __call__(self):
        self.calls += 1
        step = self.script.pop(0) if len(self.script) > 1 else self.script[0]
        if isinstance(step, Exception):
            raise step
        return step


def fail_operation():
    return Operation(requests.ConnectionError("down"))


def test_defaults_match_the_values_confirmed_by_the_user():
    assert django_settings.SERVICE_RETRY_ATTEMPTS == 2
    assert django_settings.SERVICE_BREAKER_FAIL_MAX == 3
    assert django_settings.SERVICE_BREAKER_RESET_TIMEOUT == 120


@pytest.fixture
def real_defaults(settings):
    """Os valores de produção (o conftest zera a espera pra suíte ser rápida)."""
    from importlib import import_module

    base = import_module("core.settings.base")
    settings.SERVICE_RETRY_WAIT_INITIAL = base.SERVICE_RETRY_WAIT_INITIAL
    settings.SERVICE_RETRY_WAIT_MAX = base.SERVICE_RETRY_WAIT_MAX
    settings.SERVICE_RETRY_JITTER = base.SERVICE_RETRY_JITTER
    return base


def test_backoff_defaults_are_5s_initial_30s_max_with_jitter(real_defaults):
    assert real_defaults.SERVICE_RETRY_WAIT_INITIAL == 5
    assert real_defaults.SERVICE_RETRY_WAIT_MAX == 30
    assert real_defaults.SERVICE_RETRY_JITTER > 0


# --- retry -------------------------------------------------------------------


def test_success_on_the_first_attempt_calls_once():
    op = Operation(response(200))

    assert call_with_resilience("svc", op).status_code == 200
    assert op.calls == 1


@pytest.mark.parametrize(
    "transient",
    [requests.ConnectionError("x"), requests.Timeout("x"), requests.ReadTimeout("x")],
)
def test_transient_exception_is_retried_and_can_recover(transient):
    op = Operation(transient, response(200))

    assert call_with_resilience("svc", op).status_code == 200
    assert op.calls == 2


def test_5xx_is_retried_and_can_recover():
    op = Operation(response(503), response(200))

    assert call_with_resilience("svc", op).status_code == 200
    assert op.calls == 2


def test_exhausting_attempts_raises_a_project_error_carrying_the_last_response():
    op = Operation(response(500))

    with pytest.raises(TransientServiceError) as raised:
        call_with_resilience("svc", op)

    assert op.calls == 2  # 2 tentativas, confirmado pelo usuário
    assert raised.value.response.status_code == 500


def test_exhausted_connection_errors_surface_the_original_exception():
    op = fail_operation()

    with pytest.raises(requests.ConnectionError):
        call_with_resilience("svc", op)

    assert op.calls == 2


@pytest.mark.parametrize("status", [400, 401, 404, 422])
def test_client_errors_are_returned_immediately_without_retry(status):
    op = Operation(response(status))

    assert call_with_resilience("svc", op).status_code == status
    assert op.calls == 1


def test_backoff_between_attempts_grows_exponentially(settings, monkeypatch):
    settings.SERVICE_RETRY_WAIT_INITIAL = 1
    settings.SERVICE_RETRY_WAIT_MAX = 30
    slept = []
    monkeypatch.setattr(time, "sleep", slept.append)
    op = fail_operation()

    with pytest.raises(requests.ConnectionError):
        call_with_resilience("svc", op, attempts=4)

    assert op.calls == 4
    assert slept == [1, 2, 4]


def test_backoff_never_exceeds_the_configured_maximum(settings, monkeypatch):
    settings.SERVICE_RETRY_WAIT_INITIAL = 10
    settings.SERVICE_RETRY_WAIT_MAX = 15
    slept = []
    monkeypatch.setattr(time, "sleep", slept.append)

    with pytest.raises(requests.ConnectionError):
        call_with_resilience("svc", fail_operation(), attempts=4)

    assert slept == [10, 15, 15]


# --- circuit breaker ---------------------------------------------------------


def trip(service="svc", operations=3):
    for _ in range(operations):
        with pytest.raises(Exception):
            call_with_resilience(service, fail_operation())


def test_breaker_stays_closed_below_the_failure_threshold():
    trip(operations=2)

    op = Operation(response(200))
    assert call_with_resilience("svc", op).status_code == 200
    assert op.calls == 1


def test_all_retry_attempts_of_one_operation_count_as_a_single_breaker_failure():
    # 2 operações falhas x 2 tentativas = 4 tentativas, mas só 2 falhas pro
    # breaker (fail_max=3): continua fechado. Contando tentativas abriria.
    trip(operations=2)

    op = Operation(response(200))
    assert call_with_resilience("svc", op).status_code == 200


def test_breaker_opens_after_three_failed_operations_and_short_circuits():
    trip(operations=3)

    op = Operation(response(200))
    with pytest.raises(pybreaker.CircuitBreakerError):
        call_with_resilience("svc", op)

    assert op.calls == 0  # nenhuma requisição de rede sequer tentada


def test_the_failure_that_trips_the_breaker_still_reports_its_real_cause():
    trip(operations=2)

    with pytest.raises(requests.ConnectionError):  # não CircuitBreakerError
        call_with_resilience("svc", fail_operation())


def test_client_errors_never_count_toward_the_breaker():
    for _ in range(10):
        assert call_with_resilience("svc", Operation(response(400))).status_code == 400

    op = Operation(response(200))
    assert call_with_resilience("svc", op).status_code == 200


def test_a_success_resets_the_consecutive_failure_count():
    trip(operations=2)
    call_with_resilience("svc", Operation(response(200)))
    trip(operations=2)  # 2 falhas de novo, não 4 acumuladas

    assert call_with_resilience("svc", Operation(response(200))).status_code == 200


def test_after_the_cooldown_one_call_goes_through_and_success_closes_the_breaker(
    settings,
):
    settings.SERVICE_BREAKER_RESET_TIMEOUT = 1
    trip(operations=3)
    time.sleep(1.2)

    probe = Operation(response(200))
    assert call_with_resilience("svc", probe).status_code == 200  # meio-aberto
    assert probe.calls == 1
    assert (
        call_with_resilience("svc", Operation(response(200))).status_code == 200
    )  # fechou


def test_a_failed_probe_after_the_cooldown_reopens_the_breaker(settings):
    settings.SERVICE_BREAKER_RESET_TIMEOUT = 1
    trip(operations=3)
    time.sleep(1.2)

    with pytest.raises(Exception):
        call_with_resilience("svc", fail_operation())  # a chamada de teste falha

    op = Operation(response(200))
    with pytest.raises(pybreaker.CircuitBreakerError):
        call_with_resilience("svc", op)  # reabriu: cooldown recomeça
    assert op.calls == 0


def test_breaker_state_is_scoped_per_service():
    trip("service-a", operations=3)

    op = Operation(response(200))
    assert call_with_resilience("service-b", op).status_code == 200


def test_breaker_state_lives_in_redis_so_other_processes_share_it():
    trip(operations=3)

    # nenhum estado em memória do processo: uma chamada nova (como a de outro
    # processo do worker) enxerga o breaker aberto porque lê do Redis
    from core.resilience import get_redis

    assert (
        get_redis(django_settings.REDIS_URL).get("breaker:svc:pybreaker:state")
        == b"open"
    )
    with pytest.raises(pybreaker.CircuitBreakerError):
        call_with_resilience("svc", Operation(response(200)))


def test_redis_being_down_degrades_to_calls_without_a_breaker_instead_of_failing(
    settings,
):
    settings.REDIS_URL = "redis://localhost:1/1"  # ninguém escuta na porta 1

    op = Operation(response(200))

    assert call_with_resilience("svc", op).status_code == 200
    assert op.calls == 1
