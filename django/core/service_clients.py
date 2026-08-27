"""
Cliente HTTP autenticado pra chamar microsserviços (Sprint 5,
`autenticacao-service-to-service-jwt`) — hoje só o `document-generator`.

Só a infraestrutura de chamada autenticada: o endpoint Django que dispara a
geração de `.apkg` de fato (Celery task, contrato de payload) é escopo da
Sprint 9 (`PRD.md`), que só precisa importar `call_document_generator` em
vez de reimplementar a assinatura do token em cada call-site.
"""

from typing import Any

import requests
from django.conf import settings

from .service_auth import mint_service_token

DOCUMENT_GENERATOR_AUDIENCE = "document-generator"
DOCUMENT_GENERATOR_API_PREFIX = "/document-generator/v1"


def call_document_generator(method: str, path: str, **kwargs: Any) -> requests.Response:
    """
    Chama o `document-generator`, assinando um JWT de serviço novo pra essa
    request específica (nunca reaproveitado entre chamadas — expiração
    curta só é segura assim, ver `service_auth.mint_service_token`).

    Args:
        method: verbo HTTP ("GET", "POST", ...).
        path: caminho relativo a `DOCUMENT_GENERATOR_API_PREFIX`
            (ex.: "/decks/export", não o path completo).
        **kwargs: repassado direto pra `requests.request` (json, timeout,
            etc.) — `headers` é mesclado com o `Authorization` gerado aqui,
            nunca sobrescrito por um `Authorization` vindo do caller.
    """
    token = mint_service_token(audience=DOCUMENT_GENERATOR_AUDIENCE)

    headers = {**kwargs.pop("headers", {}), "Authorization": f"Bearer {token}"}
    url = f"{settings.DOCUMENT_GENERATOR_BASE_URL}{DOCUMENT_GENERATOR_API_PREFIX}{path}"

    return requests.request(method, url, headers=headers, **kwargs)
