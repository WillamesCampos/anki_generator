"""
Fixtures dos testes de decks/cards (Sprint 2). Requerem MongoDB real
rodando (`docker compose up -d mongo`) — mesma convenção da Sprint 1
(Postgres/Redis reais, nunca mockados).
"""

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.decks.infrastructure.mongodb_connection import ensure_mongodb_connection
from apps.decks.infrastructure.schemas import uuid_to_object_id

SEEDED_COLLECTIONS = (
    "cards",
    "decks",
    "categories",
    "card_reviews",
    "generation_sessions",
)


def _clear_collections():
    manager = ensure_mongodb_connection()
    for name in SEEDED_COLLECTIONS:
        collection = manager.get_collection(name)
        collection.delete_many({})


def read_raw_document(collection_name: str, entity_id):
    """Lê um documento direto do Mongo, ignorando qualquer filtro de domínio
    (ex.: `base_filter`/soft delete) — usado pra confirmar que um soft
    delete gravou `deleted_at` sem depender do próprio filtro que o esconde
    das leituras normais."""
    manager = ensure_mongodb_connection()
    collection = manager.get_collection(collection_name)
    return collection.find_one({"_id": uuid_to_object_id(entity_id)})


def backdate_deleted_at(collection_name: str, entity_id, when):
    """Força `deleted_at` pra uma data no passado — simula "já passou da
    janela de retenção de 7 dias" sem precisar esperar 7 dias de verdade."""
    manager = ensure_mongodb_connection()
    collection = manager.get_collection(collection_name)
    collection.update_one(
        {"_id": uuid_to_object_id(entity_id)}, {"$set": {"deleted_at": when}}
    )


@pytest.fixture(autouse=True)
def _clean_mongo():
    """Mongo não faz parte da transação de teste do Django — limpa manualmente."""
    _clear_collections()
    yield
    _clear_collections()


@pytest.fixture(autouse=True)
def _clear_cache():
    """Evita que o throttle de um teste vaze pro próximo (cache Redis compartilhado)."""
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def owner_a(db):
    return User.objects.create_user(
        username="deck_owner_a", email="deck_owner_a@example.com"
    )


@pytest.fixture
def owner_b(db):
    return User.objects.create_user(
        username="deck_owner_b", email="deck_owner_b@example.com"
    )


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
