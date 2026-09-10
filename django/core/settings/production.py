"""Settings de produção (VPS Hostinger, ver `<deploy_infraestrutura>` em PROMPT_REFINADO.md)."""

import os

from .base import *  # noqa: F401,F403

DEBUG = False
ALLOWED_HOSTS = [h for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",") if h]

# Domínio real da SPA (S3/CloudFront) — configurado via env quando o
# deploy do frontend acontecer (Sprint 8). Vazio por padrão: corsheaders
# nega tudo por padrão (seguro), não libera nada por engano.
CORS_ALLOWED_ORIGINS = [
    o for o in os.environ.get("DJANGO_CORS_ALLOWED_ORIGINS", "").split(",") if o
]

# `<restricao id="seed-nao-producao">`: o comando de seed (Sprint 2) DEVE checar
# esta flag e recusar rodar em produção.
DEMO_DATA_ENABLED = False

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# E-mail (recuperação de senha, PRD.md §7.1): relay SMTP do Resend —
# confirme host/porta/usuário no dashboard do Resend ao criar a conta, este
# valor segue a convenção documentada por eles no momento da escolha do
# provedor (usuário "resend", senha = API key).
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.resend.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "resend"
EMAIL_HOST_PASSWORD = os.environ["RESEND_API_KEY"]
