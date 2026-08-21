"""Settings de desenvolvimento local."""

from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# SPA (Sprint 3) roda em origem separada (Vite, porta 5173) — sem isso o
# navegador bloqueia a SPA de ler a resposta da API, mesmo com JWT válido.
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    # :4173 é o "vite preview" (build de produção servido localmente) — não é
    # o fluxo padrão (`make frontend-dev`, :5173), mas liberado também para
    # permitir testar o build real sem precisar editar isso na hora.
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]

# Habilita o comando de seed (Sprint 2) e demais ferramentas de desenvolvimento.
DEMO_DATA_ENABLED = True
