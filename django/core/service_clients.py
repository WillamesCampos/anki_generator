"""
Cliente HTTP autenticado pra chamar microsserviços (Sprint 5,
`autenticacao-service-to-service-jwt`) — hoje só o `document-generator`.

Só a infraestrutura de chamada autenticada: o endpoint Django que dispara a
geração de `.apkg` de fato (Celery task, contrato de payload) é escopo da
Sprint 11 (`PRD.md`), que só precisa importar `call_document_generator` em
vez de reimplementar a assinatura do token em cada call-site.
"""

from typing import Any

import requests
from django.conf import settings

from .resilience import call_with_resilience
from .service_auth import mint_service_token

DOCUMENT_GENERATOR_AUDIENCE = "document-generator"
DOCUMENT_GENERATOR_API_PREFIX = "/document-generator/v1"


def call_document_generator(method: str, path: str, **kwargs: Any) -> requests.Response:
    """
    Chama o `document-generator` com JWT de serviço, retry exponencial e
    circuit breaker compartilhado (Sprint 11, D3 — `core/resilience.py`).

    Cada TENTATIVA assina um JWT novo: o token dura 60 s (nunca reaproveitado,
    ver `service_auth.mint_service_token`) e uma leitura pode levar até 300 s,
    então reusar o da primeira tentativa faria a segunda falhar com 401.

    Args:
        method: verbo HTTP ("GET", "POST", ...).
        path: caminho relativo a `DOCUMENT_GENERATOR_API_PREFIX`
            (ex.: "/decks/export", não o path completo).
        **kwargs: repassado direto pra `requests.request` (json, `timeout` por
            call-site, etc.) — `headers` é mesclado com o `Authorization` gerado
            aqui, nunca sobrescrito por um `Authorization` vindo do caller.

    Returns:
        A resposta. 4xx volta na hora, sem retry (o chamador decide);
        5xx/rede esgotam as tentativas e levantam (ver `call_with_resilience`).
    """
    extra_headers = kwargs.pop("headers", {})
    url = f"{settings.DOCUMENT_GENERATOR_BASE_URL}{DOCUMENT_GENERATOR_API_PREFIX}{path}"

    def attempt() -> requests.Response:
        token = mint_service_token(audience=DOCUMENT_GENERATOR_AUDIENCE)
        headers = {**extra_headers, "Authorization": f"Bearer {token}"}
        return requests.request(method, url, headers=headers, **kwargs)

    return call_with_resilience(DOCUMENT_GENERATOR_AUDIENCE, attempt)
