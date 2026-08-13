"""Settings de desenvolvimento local."""

from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# SPA (Sprint 3) roda em origem separada (Vite, porta 5173) — sem isso o
# navegador bloqueia a SPA de ler a resposta da API, mesmo com JWT válido.
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Habilita o comando de seed (Sprint 2) e demais ferramentas de desenvolvimento.
DEMO_DATA_ENABLED = True
