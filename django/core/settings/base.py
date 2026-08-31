"""
Settings compartilhadas entre todos os ambientes.

`local.py` e `production.py` importam este módulo e sobrescrevem apenas o que
diverge por ambiente (ver `<regra_obrigatoria id="config-ambientes">` em
PROMPT_REFINADO.md). `python-dotenv` é carregado aqui, uma única vez, na
inicialização do Django.
"""

import json
import os
from datetime import timedelta
from pathlib import Path

from celery.schedules import crontab
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")

# `<regra_obrigatoria id="env-secrets">`: a SECRET_KEY DEVE vir de DJANGO_SECRET_KEY,
# nunca hardcoded.
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

DEBUG = False
ALLOWED_HOSTS: list[str] = []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",  # exigido pelo allauth
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "dj_rest_auth",
    "dj_rest_auth.registration",
    "apps.accounts",
    "apps.decks",
]

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # CorsMiddleware o mais alto possível na lista, sempre antes de
    # CommonMiddleware (recomendação da própria lib) — a SPA (Sprint 3,
    # localhost:5173 em dev) fica em origem diferente da API.
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"

# `<regra_obrigatoria id="banco-relacional-postgres">`: PostgreSQL é o único
# banco relacional aceito (auth/Permission/Group/sessões/admin/migrations) —
# SQLite NUNCA é usado, nem localmente, por paridade dev/prod. Decks/cards/
# estatísticas vivem no MongoDB (ver apps/decks/infrastructure/mongodb_config.py),
# que não passa pelo ORM do Django.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "anki_generator"),
        "USER": os.environ.get("POSTGRES_USER", "anki_generator"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

# `<regra_obrigatoria id="model-usuario">`: reaproveita o model nativo do
# Django, com email como chave única — ver apps/accounts/models.py.
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    # `<decisao_resolvida id="...">` (Sprint 1, D1 em design.md): autenticação
    # via JWT, não sessão — a SPA (S3) fica em origem separada da API.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    # `<regra_obrigatoria id="rate-limiting-circuit-breaker">`: 10 req/s por
    # usuário/cliente, usando o backend de cache Redis já configurado
    # (CACHES, mais abaixo neste arquivo).
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "user": "10/second",
        "anon": "10/second",
    },
    # Generic Views sobre decks/cards (Mongo) devolvem uma lista Python já
    # resolvida em `get_queryset()`, não um QuerySet — PageNumberPagination
    # só precisa de algo fatiável/contável, então funciona igual (ver D2 em
    # openspec/changes/sprint-2-decks-cards/design.md).
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# Access token + refresh token mais longo, com rotação a cada uso — ver D1
# em design.md da Sprint 1. A revogação (blocklist no Redis) é feita em
# apps/accounts/tokens.py, chamada explicitamente no logout.
#
# ACCESS_TOKEN_LIFETIME aumentado de 15min para 1h (Sprint 3) — a duração
# curta original tornava o fluxo de dev manual (sem tela de login ainda,
# token gerado via shell e colado no localStorage) irritante de testar.
# Não exige nenhum ajuste no blocklist de refresh token: o TTL de cada
# entrada no Redis já é calculado dinamicamente a partir do `exp` real do
# token (`apps/accounts/tokens.py:revoke_refresh_token`), nunca um valor
# fixo — então continua "acompanhando" a validade real do token sozinho,
# em vez de precisar ser sincronizado manualmente aqui.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# JWT de serviço (Sprint 5, `autenticacao-service-to-service-jwt`) — assina
# chamadas Django -> microsserviços (hoje só document-generator). Chave
# DELIBERADAMENTE separada do SIMPLE_JWT acima: um vazamento aqui não deve
# comprometer sessão de usuário, e vice-versa (ver D4 em
# openspec/changes/sprint-5-fundacoes-transversais/design.md).
#
# `SERVICE_JWT_KEYS` é um JSON `{"kid": "secret", ...}` — todas as chaves que
# este processo aceita/pode usar. `SERVICE_JWT_ACTIVE_KID` diz qual delas
# assina tokens novos. Rotação sem downtime: adiciona um kid novo a
# `SERVICE_JWT_KEYS` nos dois lados (Django e document-generator), promove
# `SERVICE_JWT_ACTIVE_KID` pra ele, depois remove o kid antigo dos dois
# lados — dois redeploys, nunca um token rejeitado no meio da troca.
SERVICE_JWT_KEYS = json.loads(os.environ.get("SERVICE_JWT_KEYS", "{}"))
SERVICE_JWT_ACTIVE_KID = os.environ.get("SERVICE_JWT_ACTIVE_KID", "")

# Nome do serviço no docker-compose (`document-generator`), resolvido via
# rede interna do Compose — não `localhost`, que só funcionaria rodando os
# dois processos fora de container.
DOCUMENT_GENERATOR_BASE_URL = os.environ.get(
    "DOCUMENT_GENERATOR_BASE_URL", "http://document-generator:8001"
)

# `USE_JWT=True` faz o dj-rest-auth delegar a emissão de token pro simplejwt
# em vez do TokenAuthentication padrão do DRF (um único token sem expiração).
# `JWT_AUTH_HTTPONLY=False` devolve o refresh token no corpo da resposta em
# vez de um cookie httponly — a SPA (origem separada, sem cookies) gerencia
# os tokens ela mesma.
REST_AUTH = {
    "USE_JWT": True,
    "JWT_AUTH_HTTPONLY": False,
    # Sem `rest_framework.authtoken`: autenticação é só JWT, sem o token
    # legado de sessão única do DRF.
    "TOKEN_MODEL": None,
}

# allauth: login por e-mail (não username) — User.USERNAME_FIELD já é
# "email"; sem isso, allauth 65.x usa o default (username), incompatível
# com o LoginSerializer do dj-rest-auth mandando {email, password}
# (confirmado via erro real: "Deve incluir 'username' e 'password'").
# Cadastro local (registro de conta nova) ainda não está conectado — só
# login, para usuários já existentes (ex.: seed) — ver PRD.md 7.1.
ACCOUNT_LOGIN_METHODS = {"email"}
# Default do allauth exige "username" no cadastro (account.W001: conflita
# com ACCOUNT_LOGIN_METHODS=email) — mesmo sem o cadastro em si conectado
# ainda, a config precisa ficar consistente. `username` não é user-facing
# neste projeto (só existe pelo REQUIRED_FIELDS do User, p/ createsuperuser).
# Formato é LISTA DE STRINGS com "*" pra obrigatório — não dict (testado:
# um dict aqui faz o parser do allauth iterar só as chaves, sem nunca ver
# "*", e todo campo vira required=False silenciosamente).
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "none"

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": os.environ.get("GOOGLE_OAUTH_CLIENT_ID", ""),
            "secret": os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", ""),
            "key": "",
        },
        "SCOPE": ["profile", "email"],
    }
}

# `<ponto_critico id="idempotencia-revisao">`: retry exponencial, DLQ e rate
# limiting já estão todos definidos — falta mapear, em change futura, quais
# operações precisam de garantia de idempotência antes de reprocessar.

# Celery + RabbitMQ (broker) + Redis (result backend/cache).
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

# `TIME_ZONE` do Django continua UTC (ver acima — grava tudo em UTC no
# banco, boa prática independente de onde o usuário está) — mas os
# horários de `CELERY_BEAT_SCHEDULE` (ex.: "meia-noite") devem respeitar o
# fuso real do usuário, não UTC. `CELERY_TIMEZONE` é lido por
# `app.config_from_object("django.conf:settings", namespace="CELERY")`
# (core/celery.py) e é só o fuso usado pra avaliar `crontab(...)` — não
# afeta como timestamps são armazenados.
CELERY_TIMEZONE = "America/Sao_Paulo"

# Primeira task Celery Beat real do projeto (Sprint 6, D4 em
# openspec/changes/sprint-6-ciclo-de-vida-deck-card/design.md) — purga
# fisicamente Deck/Card/Category soft-deletados há mais de 7 dias.
# `crontab` (não `timedelta`) de propósito: horário fixo (meia-noite,
# CELERY_TIMEZONE acima), em vez de "24h depois de o celery-beat ter
# iniciado" — que dependeria de quando o container subiu/reiniciou.
CELERY_BEAT_SCHEDULE = {
    "purge-soft-deleted-daily": {
        "task": "apps.decks.tasks.purge_soft_deleted",
        "schedule": crontab(hour=0, minute=0),
    },
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://localhost:6379/1"),
    }
}
