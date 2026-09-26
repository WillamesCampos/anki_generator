"""
Registro Redis das exportações Anki (Sprint 11, D5/D6/D7).

Duas chaves por exportação, ambas no cache Redis do Django:

- `export:by-id:{export_id}` → `{owner_id, deck_id, content_hash, status, s3_key}`.
  Criada no **disparo**, então a posse é checável já em `pending` e um id
  desconhecido/expirado é simplesmente inexistente (o status responde 404).
- `export:by-content:{owner_id}:{deck_id}:{content_hash}` → `export_id`. Índice
  do cache por conteúdo **e** lock contra geração duplicada (`cache.add` é
  um SET NX atômico). O `owner_id` faz parte da chave: nunca há
  compartilhamento entre tenants.

TTLs vêm de `settings.EXPORT_*_TTL_SECONDS`, lidos a cada chamada.
"""

import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from django.conf import settings
from django.core.cache import cache

from .exceptions import ExportRegistrationError

PENDING = "pending"
COMPLETED = "completed"
FAILED = "failed"


class ExportOutcome(Enum):
    MISS = "miss"  # nada em cache nem em andamento: enfileirar a task
    IN_PROGRESS = "in_progress"  # mesma exportação já rodando: reaproveitar o id
    HIT = "hit"  # já concluída pra esse conteúdo: sem gerar nada


@dataclass(frozen=True)
class StartResult:
    outcome: ExportOutcome
    export_id: str


def by_id_key(export_id: str) -> str:
    return f"export:by-id:{export_id}"


def by_content_key(owner_id: str, deck_id: str, content_hash: str) -> str:
    return f"export:by-content:{owner_id}:{deck_id}:{content_hash}"


def _content_key_of(record: dict) -> str:
    return by_content_key(record["owner_id"], record["deck_id"], record["content_hash"])


def get_record(export_id: str) -> Optional[dict]:
    return cache.get(by_id_key(export_id))


def start_export(owner_id: str, deck_id: str, content_hash: str) -> StartResult:
    """
    Registra uma nova exportação ou reaproveita a existente do mesmo conteúdo.

    O registro `by-id` é gravado antes do ponteiro de conteúdo: quem ler o
    ponteiro sempre encontra o registro. Se o `SET NX` perde a corrida, o
    registro recém-criado é descartado e devolve-se o id já existente.
    """
    ttl = settings.EXPORT_PENDING_TTL_SECONDS
    export_id = str(uuid.uuid4())
    cache.set(
        by_id_key(export_id),
        {
            "owner_id": owner_id,
            "deck_id": deck_id,
            "content_hash": content_hash,
            "status": PENDING,
            "s3_key": None,
        },
        ttl,
    )
    content_key = by_content_key(owner_id, deck_id, content_hash)

    for _ in range(3):
        if cache.add(content_key, export_id, ttl):
            return StartResult(ExportOutcome.MISS, export_id)

        existing_id = cache.get(content_key)
        existing = get_record(existing_id) if existing_id else None
        if existing is None or existing["status"] == FAILED:
            # ponteiro órfão (o registro expirou antes dele): solta e tenta de novo
            cache.delete(content_key)
            continue

        cache.delete(by_id_key(export_id))
        outcome = (
            ExportOutcome.HIT
            if existing["status"] == COMPLETED
            else ExportOutcome.IN_PROGRESS
        )
        return StartResult(outcome, existing_id)

    cache.delete(by_id_key(export_id))
    raise ExportRegistrationError(
        "could not register the export: content index kept changing"
    )


def touch_pending(export_id: str) -> bool:
    """Renova o TTL do `pending` (registro e ponteiro) ao iniciar a task.
    `False` se o registro já expirou enquanto esperava na fila."""
    record = get_record(export_id)
    if record is None:
        return False
    ttl = settings.EXPORT_PENDING_TTL_SECONDS
    cache.touch(by_id_key(export_id), ttl)
    cache.touch(_content_key_of(record), ttl)
    return True


def mark_completed(export_id: str, s3_key: str) -> bool:
    record = get_record(export_id)
    if record is None:
        return False
    ttl = settings.EXPORT_COMPLETED_TTL_SECONDS
    cache.set(
        by_id_key(export_id), {**record, "status": COMPLETED, "s3_key": s3_key}, ttl
    )
    cache.touch(_content_key_of(record), ttl)
    return True


def mark_failed(export_id: str) -> bool:
    """Marca como falha e libera o ponteiro de conteúdo (só se ainda for o
    desta exportação), pra uma nova tentativa poder ser enfileirada."""
    record = get_record(export_id)
    if record is None:
        return False
    cache.set(
        by_id_key(export_id),
        {**record, "status": FAILED},
        settings.EXPORT_FAILED_TTL_SECONDS,
    )
    content_key = _content_key_of(record)
    if cache.get(content_key) == export_id:
        cache.delete(content_key)
    return True
