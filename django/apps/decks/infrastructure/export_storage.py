"""
Armazenamento das exportações Anki no S3 (Sprint 11, D1/D2).

O bucket é privado; o download é sempre por URL pré-assinada de curta duração,
**assinada localmente a cada consulta** (HMAC — sem chamada de rede ao S3) e
nunca guardada nem logada. As credenciais vêm do ambiente (`AWS_ACCESS_KEY_ID`
/`AWS_SECRET_ACCESS_KEY`), nunca de settings ou do código.
"""

import unicodedata
from urllib.parse import quote

import boto3
from botocore.config import Config
from django.conf import settings


def export_key(owner_id: str, deck_id: str, content_hash: str) -> str:
    """Chave escopada por dono e deck; o hash identifica o conteúdo (D2/D7)."""
    return f"exports/{owner_id}/{deck_id}/{content_hash}.apkg"


def _client(endpoint_url: str = ""):
    return boto3.client(
        "s3",
        region_name=settings.AWS_S3_REGION_NAME,
        endpoint_url=endpoint_url or None,
        config=Config(
            signature_version="s3v4",
            # MinIO (dev) exige path-style; na AWS real o padrão serve
            s3={"addressing_style": "path" if endpoint_url else "auto"},
        ),
    )


def upload_apkg(key: str, data: bytes) -> None:
    """Grava o `.apkg` no bucket. Erros do S3 sobem (`ClientError`) — quem
    chama decide como tratá-los (a task marca a exportação como falha)."""
    _client(settings.AWS_S3_ENDPOINT_URL).put_object(
        Bucket=settings.AWS_S3_EXPORT_BUCKET,
        Key=key,
        Body=data,
        ContentType="application/octet-stream",
    )


def _content_disposition(download_name: str) -> str:
    ascii_name = (
        unicodedata.normalize("NFKD", download_name).encode("ascii", "ignore").decode()
        or "deck.apkg"
    )
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(download_name)}"


def presigned_download_url(key: str, download_name: str = "") -> str:
    """URL de download válida por `EXPORT_DOWNLOAD_URL_TTL_SECONDS` (15 min)."""
    params = {"Bucket": settings.AWS_S3_EXPORT_BUCKET, "Key": key}
    if download_name:
        params["ResponseContentDisposition"] = _content_disposition(download_name)

    # o host assinado precisa ser alcançável por quem vai abrir a URL
    endpoint = settings.AWS_S3_PUBLIC_ENDPOINT_URL or settings.AWS_S3_ENDPOINT_URL
    return _client(endpoint).generate_presigned_url(
        "get_object",
        Params=params,
        ExpiresIn=settings.EXPORT_DOWNLOAD_URL_TTL_SECONDS,
    )
