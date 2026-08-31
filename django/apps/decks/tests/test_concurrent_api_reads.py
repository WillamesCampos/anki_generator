"""Regressão da abertura de deck pela SPA (Sprint 7).

O detalhe dispara leituras de Deck e Card próximas entre si. O bridge antigo
(`async_to_sync` por chamada) criava um event loop diferente para cada request;
como o singleton do Motor guardava um único client, uma chamada sobrescrevia a
conexão da outra e produzia `RepositoryError`/500 de forma intermitente.
"""

from concurrent.futures import ThreadPoolExecutor

import pytest
from django.core.cache import cache
from django.db import connection

from .conftest import api_client_for


def get_and_close(client, path):
    try:
        return client.get(path)
    finally:
        connection.close()


@pytest.mark.django_db(transaction=True)
def test_deck_detail_and_card_count_support_concurrent_reads(client_a, owner_a):
    create_response = client_a.post(
        "/api/v1/decks/",
        {"title": "Deck concorrente"},
        format="json",
    )
    assert create_response.status_code == 201
    deck_id = create_response.data["id"]

    cache.clear()
    detail_client = api_client_for(owner_a)
    count_client = api_client_for(owner_a)

    with ThreadPoolExecutor(max_workers=2) as executor:
        detail_future = executor.submit(
            get_and_close,
            detail_client,
            f"/api/v1/decks/{deck_id}/",
        )
        count_future = executor.submit(
            get_and_close,
            count_client,
            f"/api/v1/cards/count/?deck_id={deck_id}",
        )

    assert detail_future.result().status_code == 200
    assert count_future.result().status_code == 200
