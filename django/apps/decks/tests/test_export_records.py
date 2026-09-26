"""Registro Redis das exportações (Sprint 11, D5/D6/D7): guarda a posse desde
o disparo, serve de índice de cache por conteúdo e de lock contra geração
duplicada. Redis real, como o resto da suíte — nunca mockado."""

import time

import pytest
from django.core.cache import cache

from apps.decks.infrastructure import export_records
from apps.decks.infrastructure.export_records import (
    COMPLETED,
    FAILED,
    PENDING,
    ExportOutcome,
)

HASH = "a" * 64
DECK = "deck-1"


def start(owner="1", deck=DECK, content_hash=HASH):
    return export_records.start_export(owner, deck, content_hash)


def test_first_request_is_a_miss_and_records_owner_as_pending():
    result = start(owner="7")

    assert result.outcome == ExportOutcome.MISS
    record = export_records.get_record(result.export_id)
    assert record["status"] == PENDING
    assert record["owner_id"] == "7"
    assert record["deck_id"] == DECK
    assert record["content_hash"] == HASH


def test_same_content_while_pending_shares_the_same_export():
    first = start()

    second = start()

    assert second.outcome == ExportOutcome.IN_PROGRESS
    assert second.export_id == first.export_id


def test_same_content_after_completion_is_a_cache_hit():
    first = start()
    export_records.mark_completed(first.export_id, "exports/1/deck-1/hash.apkg")

    second = start()

    assert second.outcome == ExportOutcome.HIT
    assert second.export_id == first.export_id
    record = export_records.get_record(first.export_id)
    assert record["status"] == COMPLETED
    assert record["s3_key"] == "exports/1/deck-1/hash.apkg"


def test_changed_content_is_a_new_miss():
    first = start(content_hash="a" * 64)
    export_records.mark_completed(first.export_id, "k")

    second = start(content_hash="b" * 64)

    assert second.outcome == ExportOutcome.MISS
    assert second.export_id != first.export_id


def test_identical_content_of_two_tenants_is_never_shared():
    mine = start(owner="1")
    export_records.mark_completed(mine.export_id, "k")

    theirs = start(owner="2")

    assert theirs.outcome == ExportOutcome.MISS
    assert theirs.export_id != mine.export_id
    assert export_records.get_record(theirs.export_id)["owner_id"] == "2"


def test_failure_releases_the_content_so_it_can_be_retried():
    first = start()

    export_records.mark_failed(first.export_id)

    assert export_records.get_record(first.export_id)["status"] == FAILED
    retry = start()
    assert retry.outcome == ExportOutcome.MISS
    assert retry.export_id != first.export_id


def test_failure_of_an_old_export_does_not_release_a_newer_one():
    old = start()
    export_records.mark_failed(old.export_id)
    newer = start()

    export_records.mark_failed(old.export_id)  # falha tardia/repetida da antiga

    assert start().export_id == newer.export_id


def test_unknown_export_id_has_no_record():
    assert export_records.get_record("00000000-0000-0000-0000-000000000000") is None


def test_stale_content_pointer_without_a_record_is_recovered():
    first = start()
    cache.delete(
        export_records.by_id_key(first.export_id)
    )  # registro expirou, ponteiro ficou

    second = start()

    assert second.outcome == ExportOutcome.MISS
    assert second.export_id != first.export_id


def test_touch_pending_renews_the_ttl_of_record_and_pointer(settings):
    settings.EXPORT_PENDING_TTL_SECONDS = 2
    first = start()

    time.sleep(1.2)
    assert export_records.touch_pending(first.export_id) is True
    time.sleep(1.2)  # sem o touch, os 2 s originais já teriam vencido

    assert export_records.get_record(first.export_id) is not None
    assert start().export_id == first.export_id


def test_touch_pending_reports_a_record_that_already_expired():
    assert export_records.touch_pending("00000000-0000-0000-0000-000000000000") is False


def test_completed_record_uses_the_completed_ttl(settings):
    settings.EXPORT_COMPLETED_TTL_SECONDS = 1
    first = start()

    export_records.mark_completed(first.export_id, "k")
    time.sleep(1.3)

    assert export_records.get_record(first.export_id) is None
    assert start().outcome == ExportOutcome.MISS


def test_registration_gives_up_with_a_project_error_if_the_index_keeps_changing():
    from unittest.mock import patch

    from core.exceptions import AppError

    with (
        patch.object(export_records.cache, "add", return_value=False),
        patch.object(export_records.cache, "get", return_value=None),
    ):
        with pytest.raises(export_records.ExportRegistrationError) as raised:
            start()

    assert isinstance(raised.value, AppError)
    assert raised.value.code == "export_registration_failed"
