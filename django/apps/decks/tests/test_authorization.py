"""
Autorização por `Group` nas views de decks/cards/categories/reviews (Sprint 5,
`permissoes-grupo-sem-contenttype`) — substitui `IsAuthenticated` puro. Ver
openspec/changes/sprint-5-fundacoes-transversais/specs/group-based-authorization/spec.md.
"""

import pytest

from .conftest import api_client_for


@pytest.mark.django_db
def test_user_in_standard_user_group_can_access_decks(client_a):
    response = client_a.get("/api/v1/decks/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_user_without_authorized_group_is_denied_with_403(owner_a):
    owner_a.groups.clear()
    client = api_client_for(owner_a)

    response = client.get("/api/v1/decks/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_unauthenticated_request_is_401_not_403():
    from rest_framework.test import APIClient

    response = APIClient().get("/api/v1/decks/")

    assert response.status_code == 401


@pytest.mark.django_db
def test_user_without_group_is_denied_on_card_review_endpoint(client_a, owner_a):
    deck_response = client_a.post("/api/v1/decks/", {"title": "Deck"}, format="json")
    deck_id = deck_response.data["id"]
    card_response = client_a.post(
        "/api/v1/cards/",
        {
            "front": "network",
            "back": "rede",
            "front_description": "The network is down today.",
            "back_description": "A rede esta fora do ar hoje.",
            "deck_id": deck_id,
        },
        format="json",
    )
    card_id = card_response.data["id"]

    owner_a.groups.clear()
    client_without_group = api_client_for(owner_a)

    response = client_without_group.post(
        f"/api/v1/cards/{card_id}/review/", {"rating": "good"}, format="json"
    )

    assert response.status_code == 403
