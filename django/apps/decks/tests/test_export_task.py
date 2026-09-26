"""Task Celery de exportação (Sprint 11, D1/D5/D7). O `document-generator` é
o único ponto isolado (fronteira HTTP de outro serviço); Redis e S3 (`moto`)
são reais/fakes de verdade e o resultado é verificado neles."""

import time
from unittest.mock import patch

import pytest
import requests

from apps.decks import tasks
from apps.decks.infrastructure import export_records, export_storage
from apps.decks.infrastructure.export_records import COMPLETED, FAILED, ExportOutcome
from apps.decks.tasks import export_deck_task

OWNER = "7"
DECK = "0b0f0b1e-6f6d-4d8e-9c47-2f1f5f0a1111"
HASH = "c" * 64
PAYLOAD = {
    "deck_id": DECK,
    "deck_title": "Inglês",
    "cards": [
        {
            "id": "c1a1c1a1-0000-4000-8000-000000000001",
            "front": "hello",
            "back": "olá",
            "front_description": "Hello, how are you?",
            "back_description": "Olá, como vai você?",
        }
    ],
}
KEY = export_storage.export_key(OWNER, DECK, HASH)


def http_response(status=200, content=b"PK\x03\x04-apkg"):
    response = requests.Response()
    response.status_code = status
    response._content = content
    return response


def run_task(export_id):
    return export_deck_task(export_id, OWNER, DECK, HASH, PAYLOAD)


@pytest.fixture
def pending_export():
    return export_records.start_export(OWNER, DECK, HASH).export_id


def object_exists(s3, key):
    return "Contents" in s3.list_objects_v2(Bucket="anki-exports-test", Prefix=key)


def test_success_uploads_the_apkg_and_marks_the_export_completed(
    s3_bucket, pending_export
):
    with patch.object(
        tasks, "call_document_generator", return_value=http_response()
    ) as call:
        result = run_task(pending_export)

    assert result == {"export_id": pending_export, "status": COMPLETED}
    stored = s3_bucket.get_object(Bucket="anki-exports-test", Key=KEY)["Body"].read()
    assert stored == b"PK\x03\x04-apkg"
    record = export_records.get_record(pending_export)
    assert record["status"] == COMPLETED and record["s3_key"] == KEY
    # cache hit passa a valer pra esse conteúdo
    assert export_records.start_export(OWNER, DECK, HASH).outcome == ExportOutcome.HIT
    method, path = call.call_args.args
    assert (method, path) == ("POST", "/decks/export")
    assert call.call_args.kwargs["json"] == PAYLOAD


def test_export_call_uses_its_own_long_read_timeout(s3_bucket, pending_export):
    with patch.object(
        tasks, "call_document_generator", return_value=http_response()
    ) as call:
        run_task(pending_export)

    connect_timeout, read_timeout = call.call_args.kwargs["timeout"]
    assert read_timeout == 300  # 100 cards de gTTS levam 81-114 s (medido)
    assert connect_timeout < read_timeout


@pytest.mark.parametrize(
    "failure",
    [
        {"side_effect": requests.ConnectionError("document-generator fora do ar")},
        {"side_effect": requests.Timeout("read timeout")},
        {"return_value": http_response(status=500, content=b"boom")},
        {"return_value": http_response(status=400, content=b"cards vazios")},
        {"return_value": http_response(status=401, content=b"invalid jwt")},
    ],
)
def test_generator_failure_marks_failed_uploads_nothing_and_allows_retry(
    s3_bucket, pending_export, failure
):
    with patch.object(tasks, "call_document_generator", **failure):
        result = run_task(pending_export)

    assert result == {"export_id": pending_export, "status": FAILED}
    assert export_records.get_record(pending_export)["status"] == FAILED
    assert not object_exists(s3_bucket, KEY)
    assert export_records.start_export(OWNER, DECK, HASH).outcome == ExportOutcome.MISS


def test_s3_upload_failure_marks_the_export_failed(s3_bucket, settings, pending_export):
    settings.AWS_S3_EXPORT_BUCKET = "bucket-that-does-not-exist"

    with patch.object(tasks, "call_document_generator", return_value=http_response()):
        result = run_task(pending_export)

    assert result["status"] == FAILED
    assert export_records.get_record(pending_export)["status"] == FAILED


def test_task_that_starts_after_its_record_expired_generates_nothing(s3_bucket):
    with patch.object(tasks, "call_document_generator") as call:
        result = export_deck_task(
            "00000000-0000-0000-0000-000000000000", OWNER, DECK, HASH, PAYLOAD
        )

    assert result["status"] == "expired"
    call.assert_not_called()
    assert not object_exists(s3_bucket, KEY)


def test_task_start_renews_the_pending_ttl(s3_bucket, settings):
    settings.EXPORT_PENDING_TTL_SECONDS = 2
    export_id = export_records.start_export(OWNER, DECK, HASH).export_id
    time.sleep(1.2)

    def slow_generation(*args, **kwargs):
        time.sleep(1.2)  # sem a renovação, os 2 s originais venceriam aqui
        return http_response()

    with patch.object(tasks, "call_document_generator", side_effect=slow_generation):
        result = run_task(export_id)

    assert result["status"] == COMPLETED
    assert export_records.get_record(export_id)["status"] == COMPLETED


def test_task_has_time_limits_above_the_worst_case_generation():
    # 2 tentativas x 300 s de leitura + backoff ≈ 606 s (design.md, Open Question 2)
    assert export_deck_task.soft_time_limit >= 606
    assert export_deck_task.time_limit > export_deck_task.soft_time_limit
