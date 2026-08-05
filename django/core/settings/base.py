"""
Settings compartilhadas entre todos os ambientes.

`local.py` e `production.py` importam este módulo e sobrescrevem apenas o que
diverge por ambiente (ver `<regra_obrigatoria id="config-ambientes">` em
PROMPT_REFINADO.md). `python-dotenv` é carregado aqui, uma única vez, na
inicialização do Django.
"""

import os
from datetime import timedelta
from pathlib import Path

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
    # `<regra_obrigatoria id="rate-limiting-circuit-breaker">`: 3 req/s por
    # usuário/cliente, usando o backend de cache Redis já configurado
    # (CACHES, mais abaixo neste arquivo).
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "user": "3/second",
        "anon": "3/second",
    },
}

# Access token curto + refresh token mais longo, com rotação a cada uso —
# ver D1 em design.md desta sprint. A revogação (blocklist no Redis) é feita
# em apps/accounts/tokens.py, chamada explicitamente no logout.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

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

# allauth: login apenas via Google por enquanto (sem cadastro local por
# email/senha — fora do escopo desta sprint).
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

# Celery + RabbitMQ (broker) + Redis (result backend/cache) — fundação de
# infraestrutura desta sprint, sem tasks reais ainda.
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://localhost:6379/1"),
    }
}
