"""
Purge de registros soft-deletados (Sprint 6, D4 em
openspec/changes/sprint-6-ciclo-de-vida-deck-card/design.md).

Primeira task Celery real do projeto — Celery Beat está instalado desde a
Sprint 0 sem nunca ter executado nada. Roda diariamente via
`CELERY_BEAT_SCHEDULE` (`core/settings/base.py`), removendo fisicamente
`Deck`/`Card`/`Category` cuja `deleted_at` passou da janela de retenção de
7 dias. Sem retry/DLQ: é idempotente por natureza (rodar de novo sobre
registros já purgados simplesmente não encontra nada pra deletar), então
`<ponto_critico id="idempotencia-revisao">` já está satisfeito por
construção pra esse caso específico.
"""

import logging
from datetime import datetime, timedelta, timezone

from celery import shared_task
from django.conf import settings

from core.service_clients import call_document_generator

from .infrastructure import export_records, export_storage
from .infrastructure.repositories.card_repository import CardRepository
from .infrastructure.repositories.category_repository import CategoryRepository
from .infrastructure.repositories.deck_repository import DeckRepository

RETENTION_DAYS = 7

logger = logging.getLogger(__name__)


@shared_task(name="apps.decks.tasks.purge_soft_deleted")
def purge_soft_deleted() -> dict:
    """
    Remove fisicamente `Deck`/`Card`/`Category` soft-deletados há mais de
    `RETENTION_DAYS` dias. Cada coleção é purgada de forma independente —
    não precisa de cascade aqui, porque o cascade (Deck→Card) já aconteceu
    no momento da exclusão (`deleted_at` setado nos dois ao mesmo tempo),
    então ambos cruzam a janela de retenção juntos.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)

    decks_purged = DeckRepository().purge_soft_deleted(cutoff)
    cards_purged = CardRepository().purge_soft_deleted(cutoff)
    categories_purged = CategoryRepository().purge_soft_deleted(cutoff)

    result = {
        "decks_purged": decks_purged,
        "cards_purged": cards_purged,
        "categories_purged": categories_purged,
    }
    logger.info("purge_soft_deleted concluído: %s", result)

    return result


@shared_task(
    name="apps.decks.tasks.export_deck",
    soft_time_limit=settings.EXPORT_TASK_SOFT_TIME_LIMIT,
    time_limit=settings.EXPORT_TASK_TIME_LIMIT,
)
def export_deck_task(
    export_id: str, owner_id: str, deck_id: str, content_hash: str, payload: dict
) -> dict:
    """
    Gera o `.apkg` de um deck no `document-generator` e o guarda no S3
    (Sprint 11, D1/D7).

    Recebe o **snapshot** do payload (montado no `POST`) e nunca relê o
    Mongo: se o deck for editado enquanto a task espera na fila, o arquivo
    guardado sob `content_hash` continua sendo exatamente o que o hash
    descreve. Qualquer falha (rede, HTTP, S3, limite de tempo) vira
    `failed` no registro Redis e libera o conteúdo pra nova tentativa — a
    task nunca propaga a exceção pro Celery, o status é o canal de erro.
    """
    if not export_records.touch_pending(export_id):
        # o registro expirou enquanto a task esperava na fila: nada a fazer
        logger.warning("export %s expirou antes de iniciar; ignorando", export_id)
        return {"export_id": export_id, "status": "expired"}

    try:
        response = call_document_generator(
            "POST",
            "/decks/export",
            json=payload,
            timeout=(
                settings.DOCUMENT_GENERATOR_EXPORT_CONNECT_TIMEOUT,
                settings.DOCUMENT_GENERATOR_EXPORT_READ_TIMEOUT,
            ),
        )
        response.raise_for_status()

        key = export_storage.export_key(owner_id, deck_id, content_hash)
        export_storage.upload_apkg(key, response.content)
    except Exception:
        logger.exception("export %s falhou", export_id)
        export_records.mark_failed(export_id)
        return {"export_id": export_id, "status": export_records.FAILED}

    export_records.mark_completed(export_id, key)
    logger.info("export %s concluído (%s)", export_id, key)
    return {"export_id": export_id, "status": export_records.COMPLETED}
