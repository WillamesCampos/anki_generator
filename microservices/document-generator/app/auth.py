"""
Verificação do JWT de serviço (Sprint 5, `autenticacao-service-to-service-jwt`)
— autentica chamadas Django -> document-generator. Ver D4 em
openspec/changes/sprint-5-fundacoes-transversais/design.md.

Verificação é sempre LOCAL: nenhuma chamada de volta pro Django pra
confirmar o token (diferente de introspection OAuth2) — a assinatura em si
é a prova. `service_jwt_keys` (`app/config.py`) guarda o mesmo mapa
`{kid: secret}` configurado do lado Django (`SERVICE_JWT_KEYS`); qualquer
`kid` presente nesse mapa é aceito, não só o mais recente, permitindo
rotação sem downtime.
"""

import jwt
from fastapi import Request

from app.config import get_settings
from app.errors import UnauthorizedError

EXPECTED_AUDIENCE = "document-generator"


async def require_service_jwt(request: Request) -> dict:
    """
    Dependency do FastAPI — injeta em toda rota que exige autenticação
    service-to-service. Levanta `UnauthorizedError` (401) se o header
    `Authorization: Bearer <jwt>` estiver ausente, malformado, com
    assinatura inválida, expirado, `aud` incorreto, ou `kid` desconhecido.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise UnauthorizedError("Missing bearer token.")

    token = auth_header.removeprefix("Bearer ").strip()

    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("Malformed service token.") from exc

    kid = unverified_header.get("kid")
    known_keys = get_settings().service_jwt_keys
    secret = known_keys.get(kid) if kid else None
    if not secret:
        raise UnauthorizedError("Unknown signing key (kid).")

    try:
        claims = jwt.decode(token, secret, algorithms=["HS256"], audience=EXPECTED_AUDIENCE)
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("Invalid or expired service token.") from exc

    return claims
