"""
Emissão de JWT de serviço para chamadas Django -> microsserviços (Sprint 5,
`autenticacao-service-to-service-jwt`). Ver D4 em
openspec/changes/sprint-5-fundacoes-transversais/design.md.

Cada par emissor/verificador tem seu próprio conjunto de chaves — hoje só
existe o par Django -> document-generator. As chaves nunca são o
`DJANGO_SECRET_KEY`/`SIMPLE_JWT` de usuário: são um segredo à parte, só
compartilhado entre os dois lados desse canal específico
(`SERVICE_JWT_KEYS`/`SERVICE_JWT_ACTIVE_KID`, ver core/settings/base.py).

Verificação é sempre local do lado de quem recebe (sem round-trip de volta
pro Django) — por isso não existe aqui uma função "verify", só emissão.
"""

import time
import uuid

import jwt
from django.conf import settings

SERVICE_ISSUER = "django-core"
TOKEN_TTL_SECONDS = 60


def mint_service_token(audience: str) -> str:
    """
    Gera um JWT de serviço (HS256) de curta duração, assinado com a chave
    ativa (`SERVICE_JWT_ACTIVE_KID`) — mintado na hora de cada chamada, não
    cacheado (a expiração curta só é segura porque não existe reuso).

    Args:
        audience: nome do serviço de destino (claim `aud`), ex.:
            "document-generator". O verificador rejeita tokens cujo `aud`
            não seja o próprio nome dele.

    Raises:
        ImproperlyConfigured: se `SERVICE_JWT_ACTIVE_KID` não tiver uma
            chave correspondente em `SERVICE_JWT_KEYS` — falha alto e cedo
            em vez de assinar com um segredo ausente.
    """
    from django.core.exceptions import ImproperlyConfigured

    active_kid = settings.SERVICE_JWT_ACTIVE_KID
    secret = settings.SERVICE_JWT_KEYS.get(active_kid)
    if not active_kid or not secret:
        raise ImproperlyConfigured(
            "SERVICE_JWT_ACTIVE_KID precisa apontar para uma chave presente "
            "em SERVICE_JWT_KEYS."
        )

    now = int(time.time())
    payload = {
        "iss": SERVICE_ISSUER,
        "aud": audience,
        "iat": now,
        "exp": now + TOKEN_TTL_SECONDS,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, secret, algorithm="HS256", headers={"kid": active_kid})
