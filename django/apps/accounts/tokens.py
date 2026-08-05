"""
Blocklist de refresh token no Redis (D1 em design.md desta sprint): o logout
revoga o refresh token imediatamente, em vez de esperar a expiração natural
— é o que torna o JWT "não-stateless-puro" seguro o suficiente pra usar.

Reaproveita o cache Redis já configurado em `core/settings/base.py`
(`CACHES["default"]`), em vez de introduzir um componente novo.
"""

import time

from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken


def _blocklist_key(jti: str) -> str:
    return f"jwt:blocklist:{jti}"


def revoke_refresh_token(raw_token: str) -> None:
    """Marca o refresh token como revogado até sua expiração natural."""
    token = RefreshToken(raw_token)
    jti = token["jti"]
    ttl_seconds = max(int(token["exp"] - time.time()), 0)
    cache.set(_blocklist_key(jti), True, timeout=ttl_seconds)


def is_refresh_token_revoked(jti: str) -> bool:
    return cache.get(_blocklist_key(jti)) is not None
