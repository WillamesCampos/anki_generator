"""Endpoints de exportação (Sprint 11, D5/D6/D7/D9): disparo assíncrono,
cache por conteúdo, deduplicação, limites e isolamento entre tenants.

Nenhum destes testes chama o `document-generator`: o `POST` só enfileira
(`export_deck_task.delay`, único ponto isolado — fronteira do broker)."""

from unittest.mock import patch

import pytest

from apps.decks import views
from apps.decks.domain.entities.card import Card
from apps.decks.domain.entities.deck import Deck
from apps.decks.domain.services.export_payload import (
    build_export_payload,
    compute_content_hash,
)
from apps.decks.domain.value_objects.translation import Translation
from apps.decks.domain.value_objects.word import Word
from apps.decks.infrastructure import export_records
from apps.decks.infrastructure.repositories.card_repository import CardRepository
from apps.decks.infrastructure.repositories.deck_repository import DeckRepository

WORDS = ["alpha", "bravo", "charlie", "delta", "echo", "foxtrot"]


def make_deck(owner, title="Inglês básico", n_cards=2):
    owner_id = str(owner.id)
    deck = DeckRepository().save(Deck(title=title, owner_id=owner_id))
    cards = [
        CardRepository().save(
            Card(
                front=Word(WORDS[i]),
                back=Translation(f"traducao {i}"),
                front_description=f"Description of {WORDS[i]} in a sentence.",
                back_description=f"Descrição de {WORDS[i]} em uma frase.",
                owner_id=owner_id,
                deck_id=deck.id,
            )
        )
        for i in range(n_cards)
    ]
    return deck, cards


def export_url(deck):
    return f"/api/v1/decks/{deck.id}/export/"


def status_url(export_id):
    return f"/api/v1/decks/export/{export_id}/status/"


@pytest.fixture
def delay():
    with patch.object(views.export_deck_task, "delay") as mocked:
        yield mocked


@pytest.mark.django_db
def test_export_requires_authentication(delay):
    from rest_framework.test import APIClient

    deck_id = "0b0f0b1e-6f6d-4d8e-9c47-2f1f5f0a1111"

    response = APIClient().post(f"/api/v1/decks/{deck_id}/export/")

    assert response.status_code == 401
    delay.assert_not_called()


@pytest.mark.django_db
def test_owner_triggers_export_and_gets_202_without_running_the_generator(
    client_a, owner_a, delay
):
    deck, cards = make_deck(owner_a)

    with patch("apps.decks.tasks.call_document_generator") as generator:
        response = client_a.post(export_url(deck))

    assert response.status_code == 202
    assert response.json()["status"] == "pending"
    export_id = response.json()["export_id"]
    generator.assert_not_called()  # nada de chamar o microsserviço na request

    expected_payload = build_export_payload(deck, cards)
    delay.assert_called_once_with(
        export_id,
        str(owner_a.id),
        str(deck.id),
        compute_content_hash(expected_payload),
        expected_payload,
    )
    assert export_records.get_record(export_id)["owner_id"] == str(owner_a.id)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "bad_id", ["not-a-uuid", "00000000-0000-0000-0000-000000000000"]
)
def test_unknown_or_malformed_deck_is_404(client_a, delay, bad_id):
    response = client_a.post(f"/api/v1/decks/{bad_id}/export/")

    assert response.status_code == 404
    delay.assert_not_called()


@pytest.mark.django_db
def test_other_tenants_deck_is_404_like_a_missing_one(client_b, owner_a, delay):
    deck, _ = make_deck(owner_a)

    response = client_b.post(export_url(deck))

    assert response.status_code == 404
    delay.assert_not_called()


@pytest.mark.django_db
def test_deck_without_cards_is_refused_up_front(client_a, owner_a, delay):
    deck, _ = make_deck(owner_a, n_cards=0)

    response = client_a.post(export_url(deck))

    assert response.status_code == 400
    delay.assert_not_called()


@pytest.mark.django_db
def test_deck_with_only_soft_deleted_cards_counts_as_empty(client_a, owner_a, delay):
    deck, cards = make_deck(owner_a, n_cards=1)
    assert client_a.delete(f"/api/v1/cards/{cards[0].id}/").status_code == 204

    response = client_a.post(export_url(deck))

    assert response.status_code == 400
    delay.assert_not_called()


@pytest.mark.django_db
def test_deck_above_the_cap_is_refused_up_front(client_a, owner_a, delay, settings):
    settings.EXPORT_MAX_CARDS = 3
    deck, _ = make_deck(owner_a, n_cards=4)

    response = client_a.post(export_url(deck))

    assert response.status_code == 400
    assert "3" in str(response.json())
    delay.assert_not_called()


@pytest.mark.django_db
def test_deck_at_the_cap_is_accepted(client_a, owner_a, delay, settings):
    settings.EXPORT_MAX_CARDS = 3
    deck, _ = make_deck(owner_a, n_cards=3)

    assert client_a.post(export_url(deck)).status_code == 202


@pytest.mark.django_db
def test_soft_deleted_cards_are_not_in_the_exported_payload(client_a, owner_a, delay):
    deck, cards = make_deck(owner_a, n_cards=3)
    client_a.delete(f"/api/v1/cards/{cards[1].id}/")

    client_a.post(export_url(deck))

    payload = delay.call_args.args[4]
    assert [c["id"] for c in payload["cards"]] == sorted(
        [str(cards[0].id), str(cards[2].id)],
        key=lambda card_id: next(
            (c.created_at, str(c.id)) for c in cards if str(c.id) == card_id
        ),
    )


@pytest.mark.django_db
def test_second_request_while_in_progress_shares_one_generation(
    client_a, owner_a, delay
):
    deck, _ = make_deck(owner_a)

    first = client_a.post(export_url(deck))
    second = client_a.post(export_url(deck))

    assert first.status_code == second.status_code == 202
    assert first.json()["export_id"] == second.json()["export_id"]
    assert delay.call_count == 1


@pytest.mark.django_db
def test_unchanged_deck_after_completion_is_a_200_cache_hit_without_a_task(
    client_a, owner_a, delay
):
    deck, _ = make_deck(owner_a)
    first = client_a.post(export_url(deck)).json()["export_id"]
    export_records.mark_completed(first, "exports/k.apkg")
    delay.reset_mock()

    response = client_a.post(export_url(deck))

    assert response.status_code == 200
    assert response.json() == {"export_id": first, "status": "completed"}
    delay.assert_not_called()


@pytest.mark.django_db
def test_editing_a_card_invalidates_the_cache(client_a, owner_a, delay):
    deck, cards = make_deck(owner_a)
    first = client_a.post(export_url(deck)).json()["export_id"]
    export_records.mark_completed(first, "exports/k.apkg")

    edit = client_a.patch(
        f"/api/v1/cards/{cards[0].id}/", {"back": "editada"}, format="json"
    )
    assert edit.status_code == 200
    response = client_a.post(export_url(deck))

    assert response.status_code == 202
    assert response.json()["export_id"] != first


@pytest.mark.django_db
def test_studying_a_card_does_not_invalidate_the_cache(client_a, owner_a, delay):
    deck, cards = make_deck(owner_a)
    first = client_a.post(export_url(deck)).json()["export_id"]
    export_records.mark_completed(first, "exports/k.apkg")

    review = client_a.post(
        f"/api/v1/cards/{cards[0].id}/review/", {"rating": "good"}, format="json"
    )
    assert review.status_code == 201
    response = client_a.post(export_url(deck))

    assert response.status_code == 200
    assert response.json()["export_id"] == first


@pytest.mark.django_db
def test_identical_decks_of_two_tenants_are_generated_separately(
    client_a, client_b, owner_a, owner_b, delay
):
    deck_a, _ = make_deck(owner_a)
    deck_b, _ = make_deck(owner_b)

    a = client_a.post(export_url(deck_a)).json()["export_id"]
    b = client_b.post(export_url(deck_b)).json()["export_id"]

    assert a != b
    assert delay.call_count == 2


@pytest.mark.django_db
def test_broker_failure_after_registering_releases_the_export(client_a, owner_a):
    deck, _ = make_deck(owner_a)

    with patch.object(
        views.export_deck_task, "delay", side_effect=ConnectionError("broker")
    ):
        response = client_a.post(export_url(deck))

    assert response.status_code == 503
    # o conteúdo não fica travado em "pending" sem task: dá pra tentar de novo
    with patch.object(views.export_deck_task, "delay") as retry_delay:
        again = client_a.post(export_url(deck))
    assert again.status_code == 202
    retry_delay.assert_called_once()


# --- GET /api/v1/decks/export/{export_id}/status/ ------------------------------


@pytest.mark.django_db
def test_owner_polls_a_pending_export_without_a_download_url(client_a, owner_a, delay):
    deck, _ = make_deck(owner_a)
    export_id = client_a.post(export_url(deck)).json()["export_id"]

    response = client_a.get(status_url(export_id))

    assert response.status_code == 200
    assert response.json() == {"export_id": export_id, "status": "pending"}


@pytest.mark.django_db
def test_owner_polls_a_completed_export_and_gets_a_fresh_presigned_url(
    client_a, owner_a, delay, s3_bucket
):
    deck, _ = make_deck(owner_a)
    export_id = client_a.post(export_url(deck)).json()["export_id"]
    key = f"exports/{owner_a.id}/{deck.id}/somehash.apkg"
    export_records.mark_completed(export_id, key)

    response = client_a.get(status_url(export_id))

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "completed"
    assert "X-Amz-Expires=900" in body["download_url"]
    assert key in body["download_url"]


@pytest.mark.django_db
def test_owner_polls_a_failed_export(client_a, owner_a, delay):
    deck, _ = make_deck(owner_a)
    export_id = client_a.post(export_url(deck)).json()["export_id"]
    export_records.mark_failed(export_id)

    response = client_a.get(status_url(export_id))

    assert response.status_code == 200
    assert response.json() == {"export_id": export_id, "status": "failed"}


@pytest.mark.django_db
@pytest.mark.parametrize("state", ["pending", "completed"])
def test_other_tenant_gets_404_even_while_pending(
    client_a, client_b, owner_a, delay, s3_bucket, state
):
    deck, _ = make_deck(owner_a)
    export_id = client_a.post(export_url(deck)).json()["export_id"]
    if state == "completed":
        export_records.mark_completed(export_id, "exports/k.apkg")

    response = client_b.get(status_url(export_id))

    assert response.status_code == 404
    assert "download_url" not in response.content.decode()


@pytest.mark.django_db
def test_unknown_or_expired_export_id_is_a_terminal_404(client_a):
    response = client_a.get(status_url("00000000-0000-0000-0000-000000000000"))

    assert response.status_code == 404


@pytest.mark.django_db
def test_not_found_looks_identical_for_unknown_and_foreign_ids(
    client_a, client_b, owner_a, delay
):
    deck, _ = make_deck(owner_a)
    foreign = client_a.post(export_url(deck)).json()["export_id"]

    unknown = client_b.get(status_url("00000000-0000-0000-0000-000000000000"))
    denied = client_b.get(status_url(foreign))

    assert unknown.status_code == denied.status_code == 404
    assert unknown.json() == denied.json()
