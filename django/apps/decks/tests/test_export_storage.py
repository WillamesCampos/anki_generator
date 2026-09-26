"""Armazenamento das exportações no S3 (Sprint 11, D1/D2), com S3 falso
(`moto`). Bucket privado, chave escopada por dono/deck/conteúdo e URL
pré-assinada de 15 minutos gerada localmente a cada consulta."""

from urllib.parse import parse_qs, urlparse

import pytest
from botocore.exceptions import ClientError

from apps.decks.infrastructure import export_storage


def test_export_key_is_scoped_by_owner_deck_and_content_hash():
    key = export_storage.export_key("7", "deck-1", "abc123")

    assert key == "exports/7/deck-1/abc123.apkg"


def test_upload_stores_the_exact_bytes_under_the_key(s3_bucket):
    key = export_storage.export_key("7", "deck-1", "abc123")

    export_storage.upload_apkg(key, b"PK\x03\x04-apkg-bytes")

    stored = s3_bucket.get_object(Bucket="anki-exports-test", Key=key)
    assert stored["Body"].read() == b"PK\x03\x04-apkg-bytes"


def test_upload_failure_surfaces_instead_of_being_swallowed(s3_bucket, settings):
    settings.AWS_S3_EXPORT_BUCKET = "bucket-that-does-not-exist"

    with pytest.raises(ClientError):
        export_storage.upload_apkg("exports/1/d/h.apkg", b"x")


def test_presigned_url_points_to_the_key_and_expires_in_15_minutes(s3_bucket):
    url = export_storage.presigned_download_url("exports/7/deck-1/abc123.apkg")

    parsed = urlparse(url)
    assert "anki-exports-test" in url
    assert parsed.path.endswith("exports/7/deck-1/abc123.apkg")
    assert parse_qs(parsed.query)["X-Amz-Expires"] == ["900"]


def test_presigned_url_signing_needs_no_network_call_to_s3(settings, monkeypatch):
    # sem `s3_bucket` (sem mock): se assinar dependesse de rede/objeto
    # existente, este teste falharia — assinatura é local (HMAC), só precisa
    # de credenciais no ambiente.
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    settings.AWS_S3_EXPORT_BUCKET = "any-bucket"
    settings.AWS_S3_REGION_NAME = "sa-east-1"
    settings.AWS_S3_ENDPOINT_URL = ""
    settings.AWS_S3_PUBLIC_ENDPOINT_URL = ""

    url = export_storage.presigned_download_url("exports/1/d/h.apkg")

    assert url.startswith("https://")


def test_presigned_url_uses_the_public_endpoint_when_configured(s3_bucket, settings):
    # dev com MinIO: o put usa o endpoint interno (`minio:9000`), mas a URL
    # que o navegador abre precisa ser assinada com um host que ele alcança.
    settings.AWS_S3_PUBLIC_ENDPOINT_URL = "http://localhost:9000"

    url = export_storage.presigned_download_url("exports/1/d/h.apkg")

    assert url.startswith("http://localhost:9000/")


def test_presigned_url_suggests_a_friendly_download_file_name(s3_bucket):
    url = export_storage.presigned_download_url(
        "exports/1/d/h.apkg", download_name="Inglês básico.apkg"
    )

    query = parse_qs(urlparse(url).query)
    assert "attachment" in query["response-content-disposition"][0]
    assert ".apkg" in query["response-content-disposition"][0]
