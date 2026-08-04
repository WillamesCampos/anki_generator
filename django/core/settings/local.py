"""Settings de desenvolvimento local."""

from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# Habilita o comando de seed (Sprint 2) e demais ferramentas de desenvolvimento.
DEMO_DATA_ENABLED = True
