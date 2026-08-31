"""
`<regra_obrigatoria id="rate-limiting-circuit-breaker">`: 10 req/s por
usuário/cliente. Testado contra o endpoint de health (anônimo), que já
existe desde a Sprint 0 e não depende de nenhum model de produto.
"""

import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_requests_within_limit_succeed():
    client = APIClient()

    for _ in range(10):
        response = client.get("/api/v1/health/")
        assert response.status_code == 200


@pytest.mark.django_db
def test_requests_over_limit_are_rejected():
    client = APIClient()

    for _ in range(10):
        client.get("/api/v1/health/")

    response = client.get("/api/v1/health/")
    assert response.status_code == 429
