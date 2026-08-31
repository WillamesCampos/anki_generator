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

from .infrastructure.async_bridge import persistent_async_to_sync as async_to_sync
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

    decks_purged = async_to_sync(DeckRepository().purge_soft_deleted)(cutoff)
    cards_purged = async_to_sync(CardRepository().purge_soft_deleted)(cutoff)
    categories_purged = async_to_sync(CategoryRepository().purge_soft_deleted)(cutoff)

    result = {
        "decks_purged": decks_purged,
        "cards_purged": cards_purged,
        "categories_purged": categories_purged,
    }
    logger.info("purge_soft_deleted concluído: %s", result)

    return result
