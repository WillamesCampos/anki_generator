"""
Fixtures dos testes de decks/cards (Sprint 2). Requerem MongoDB real
rodando (`docker compose up -d mongo`) — mesma convenção da Sprint 1
(Postgres/Redis reais, nunca mockados).
"""

import asyncio

# test_mongodb_integration.py é um script standalone (Sprint 0, funções
# `async def` de nível de módulo, rodado via `python -m
# apps.decks.tests.test_mongodb_integration`) — não uma suíte pytest. O
# nome do arquivo/funções bate com o padrão de auto-descoberta do pytest
# por coincidência; sem essa exclusão, pytest tenta coletá-lo e falha por
# não ter suporte nativo a `async def` sem um plugin (não usamos
# pytest-asyncio, ver PRD/convenção de testes em PROMPT_REFINADO.md).
collect_ignore = ["test_mongodb_integration.py"]

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.decks.infrastructure.mongodb_connection import ensure_mongodb_connection

SEEDED_COLLECTIONS = ("cards", "decks", "categories", "card_reviews", "generation_sessions")


def run_async(coro):
    return asyncio.run(coro)


async def _clear_collections():
    manager = await ensure_mongodb_connection()
    for name in SEEDED_COLLECTIONS:
        collection = await manager.get_collection(name)
        await collection.delete_many({})


@pytest.fixture(autouse=True)
def _clean_mongo():
    """Mongo não faz parte da transação de teste do Django — limpa manualmente."""
    run_async(_clear_collections())
    yield
    run_async(_clear_collections())


@pytest.fixture(autouse=True)
def _clear_cache():
    """Evita que o throttle de um teste vaze pro próximo (cache Redis compartilhado)."""
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def owner_a(db):
    return User.objects.create_user(username="deck_owner_a", email="deck_owner_a@example.com")


@pytest.fixture
def owner_b(db):
    return User.objects.create_user(username="deck_owner_b", email="deck_owner_b@example.com")


def api_client_for(user: User) -> APIClient:
    token = str(RefreshToken.for_user(user).access_token)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def client_a(owner_a) -> APIClient:
    return api_client_for(owner_a)


@pytest.fixture
def client_b(owner_b) -> APIClient:
    return api_client_for(owner_b)
