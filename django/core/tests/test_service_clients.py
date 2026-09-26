"""`call_document_generator` com resiliência (Sprint 11, tarefa 2.3): mesma
assinatura pública da Sprint 5, agora com retry/circuit breaker e um JWT de
serviço novo a cada tentativa."""

import inspect
from unittest.mock import patch

import jwt
import pybreaker
import pytest
import requests

from core.service_clients import call_document_generator


@pytest.fixture(autouse=True)
def _service_keys(settings):
    settings.SERVICE_JWT_KEYS = {"v1": "test-secret"}
    settings.SERVICE_JWT_ACTIVE_KID = "v1"


def http_response(status=200):
    r = requests.Response()
    r.status_code = status
    r._content = b"ok"
    return r


def test_public_signature_is_unchanged():
    params = inspect.signature(call_document_generator).parameters

    assert list(params) == ["method", "path", "kwargs"]


def test_transient_failure_is_retried_transparently():
    with patch("core.service_clients.requests.request") as request:
        request.side_effect = [requests.ConnectionError("down"), http_response(200)]

        result = call_document_generator("POST", "/decks/export", json={"a": 1})

    assert result.status_code == 200
    assert request.call_count == 2


def test_each_attempt_signs_a_fresh_service_token():
    # o JWT dura 60 s e a leitura pode levar até 300 s: reusar o token da
    # primeira tentativa faria a segunda falhar com 401
    with patch("core.service_clients.requests.request") as request:
        request.side_effect = [requests.Timeout("slow"), http_response(200)]

        call_document_generator("POST", "/decks/export")

    tokens = [
        call.kwargs["headers"]["Authorization"].removeprefix("Bearer ")
        for call in request.call_args_list
    ]
    jtis = [
        jwt.decode(
            t, "test-secret", algorithms=["HS256"], audience="document-generator"
        )["jti"]
        for t in tokens
    ]
    assert len(set(jtis)) == 2


def test_request_kwargs_including_the_per_call_timeout_are_forwarded():
    with patch(
        "core.service_clients.requests.request", return_value=http_response()
    ) as request:
        call_document_generator(
            "POST", "/decks/export", json={"x": 1}, timeout=(5, 300)
        )

    assert request.call_args.kwargs["timeout"] == (5, 300)
    assert request.call_args.kwargs["json"] == {"x": 1}
    assert request.call_args.args[:2] == (
        "POST",
        "http://document-generator:8001/document-generator/v1/decks/export",
    )


def test_client_error_is_returned_without_retry():
    with patch(
        "core.service_clients.requests.request", return_value=http_response(401)
    ) as request:
        result = call_document_generator("POST", "/decks/export")

    assert result.status_code == 401
    assert request.call_count == 1


def test_repeated_outages_open_the_shared_breaker_for_every_call_site():
    with patch(
        "core.service_clients.requests.request",
        side_effect=requests.ConnectionError("down"),
    ):
        for _ in range(3):
            with pytest.raises(requests.ConnectionError):
                call_document_generator("POST", "/decks/export")

    with patch("core.service_clients.requests.request") as request:
        with pytest.raises(pybreaker.CircuitBreakerError):
            call_document_generator(
                "POST", "/documents/pdf"
            )  # outro call-site, mesmo serviço

    request.assert_not_called()
