"""
`manage.py check_export_storage` — valida de ponta a ponta o S3 das exportações
Anki (Sprint 11): grava um arquivo de teste sob `exports/_healthcheck/`, baixa
por URL pré-assinada e apaga. Confirma bucket, região, credenciais e as três
permissões IAM que o sistema usa (`s3:PutObject`, `s3:GetObject`,
`s3:DeleteObject`), e traduz os erros típicos da AWS em instruções.
"""

import uuid

import requests
from botocore.exceptions import ClientError, NoCredentialsError
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.decks.infrastructure import export_storage


def _explain(error: Exception) -> str:
    bucket = settings.AWS_S3_EXPORT_BUCKET
    if isinstance(error, NoCredentialsError):
        return (
            "Credenciais AWS ausentes: defina AWS_ACCESS_KEY_ID e "
            "AWS_SECRET_ACCESS_KEY no django/.env (chaves do usuário IAM dedicado)."
        )
    if isinstance(error, ClientError):
        code = error.response.get("Error", {}).get("Code", "")
        if code in {"NoSuchBucket", "404"}:
            return f"O bucket '{bucket}' não existe (ou o nome em AWS_S3_EXPORT_BUCKET está errado)."
        if code in {"AccessDenied", "AllAccessDisabled", "403"}:
            return (
                "Acesso negado pelo IAM. O usuário precisa destas permissões no "
                f"recurso arn:aws:s3:::{bucket}/exports/* : s3:PutObject, "
                "s3:GetObject e s3:DeleteObject."
            )
        if code in {"InvalidAccessKeyId", "SignatureDoesNotMatch"}:
            return (
                "Chave de acesso inválida: confira AWS_ACCESS_KEY_ID e "
                "AWS_SECRET_ACCESS_KEY (sem espaços; a chave secreta só aparece "
                "uma vez, na criação)."
            )
        if code in {
            "PermanentRedirect",
            "301",
            "AuthorizationHeaderMalformed",
            "IllegalLocationConstraintException",
        }:
            return (
                f"O bucket '{bucket}' está em outra região que "
                f"AWS_S3_REGION_NAME='{settings.AWS_S3_REGION_NAME}'. Veja a região "
                "do bucket no console e ajuste a variável."
            )
        return f"Erro do S3 ({code}): {error}"
    return f"Falha inesperada: {error!r}"


class Command(BaseCommand):
    help = "Valida o bucket S3 das exportações (upload, URL pré-assinada, delete)."

    def handle(self, *args, **options):
        bucket = settings.AWS_S3_EXPORT_BUCKET
        if not bucket:
            raise CommandError(
                "AWS_S3_EXPORT_BUCKET não está definido: informe o nome do bucket no django/.env."
            )

        probe = uuid.uuid4().hex
        key = f"exports/_healthcheck/{probe}.txt"
        payload = f"anki-generator healthcheck {probe}".encode()
        self.stdout.write(f"Bucket: {bucket} | região: {settings.AWS_S3_REGION_NAME}")

        try:
            export_storage.upload_apkg(key, payload)
            self.stdout.write("  PutObject    OK (gravou o arquivo de teste)")

            url = export_storage.presigned_download_url(key)
            response = requests.get(url, timeout=15)
            if response.status_code != 200 or response.content != payload:
                raise CommandError(
                    f"A URL pré-assinada não devolveu o arquivo (HTTP {response.status_code}). "
                    "Verifique GetObject e, em dev com S3 local, AWS_S3_PUBLIC_ENDPOINT_URL."
                )
            self.stdout.write("  GetObject    OK (baixou pela URL pré-assinada)")

            export_storage.delete_object(key)
            self.stdout.write("  DeleteObject OK (apagou o arquivo de teste)")
        except CommandError:
            raise
        except Exception as error:  # noqa: BLE001 — traduzido em mensagem acionável
            raise CommandError(_explain(error)) from error
        finally:
            try:  # melhor esforço: não deixa o arquivo de teste pra trás
                export_storage.delete_object(key)
            except Exception:  # noqa: BLE001
                pass

        self.stdout.write(self.style.SUCCESS("OK — o S3 das exportações está pronto."))
