"""`manage.py check_export_storage` (Sprint 11): valida de ponta a ponta o
bucket, a região e as credenciais IAM configuradas — grava, baixa por URL
pré-assinada e apaga um arquivo de teste — com mensagens acionáveis pros erros
típicos de configuração da AWS."""

from io import StringIO

import pytest
from botocore.exceptions import ClientError
from django.core.management import CommandError, call_command

from apps.decks.infrastructure import export_storage


def run():
    out = StringIO()
    call_command("check_export_storage", stdout=out)
    return out.getvalue()


def objects(s3):
    return s3.list_objects_v2(Bucket="anki-exports-test").get("Contents", [])


def test_healthy_setup_round_trips_and_leaves_the_bucket_clean(s3_bucket):
    output = run()

    assert "OK" in output
    assert "PutObject" in output and "GetObject" in output and "DeleteObject" in output
    assert objects(s3_bucket) == []  # o arquivo de teste foi apagado


def test_probe_object_lives_under_the_exports_prefix(s3_bucket, monkeypatch):
    seen = []
    original = export_storage.upload_apkg
    monkeypatch.setattr(
        export_storage,
        "upload_apkg",
        lambda key, data: (seen.append(key), original(key, data))[1],
    )

    run()

    assert seen and seen[0].startswith("exports/")


def test_missing_bucket_setting_tells_which_variable_to_set(settings):
    settings.AWS_S3_EXPORT_BUCKET = ""

    with pytest.raises(CommandError, match="AWS_S3_EXPORT_BUCKET"):
        run()


def test_nonexistent_bucket_is_reported_clearly(s3_bucket, settings):
    settings.AWS_S3_EXPORT_BUCKET = "bucket-that-does-not-exist"

    with pytest.raises(CommandError, match="não existe"):
        run()


def test_access_denied_lists_the_permissions_the_iam_user_needs(s3_bucket, monkeypatch):
    def denied(key, data):
        raise ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "nope"}}, "PutObject"
        )

    monkeypatch.setattr(export_storage, "upload_apkg", denied)

    with pytest.raises(CommandError) as raised:
        run()

    message = str(raised.value)
    assert (
        "s3:PutObject" in message
        and "s3:GetObject" in message
        and "s3:DeleteObject" in message
    )


def test_region_mismatch_is_reported_with_the_configured_region(
    s3_bucket, monkeypatch, settings
):
    def wrong_region(key, data):
        raise ClientError(
            {"Error": {"Code": "PermanentRedirect", "Message": "use another endpoint"}},
            "PutObject",
        )

    monkeypatch.setattr(export_storage, "upload_apkg", wrong_region)

    with pytest.raises(CommandError, match="AWS_S3_REGION_NAME"):
        run()


def test_missing_credentials_are_reported(monkeypatch, settings):
    from botocore.exceptions import NoCredentialsError

    settings.AWS_S3_EXPORT_BUCKET = "any"

    def no_credentials(key, data):
        raise NoCredentialsError()

    monkeypatch.setattr(export_storage, "upload_apkg", no_credentials)

    with pytest.raises(CommandError, match="AWS_ACCESS_KEY_ID"):
        run()


def test_storage_can_delete_an_object(s3_bucket):
    export_storage.upload_apkg("exports/1/d/h.apkg", b"x")

    export_storage.delete_object("exports/1/d/h.apkg")

    assert objects(s3_bucket) == []
