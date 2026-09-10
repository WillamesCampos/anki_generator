"""
Comando de seed (PRD Sprint 2, 2.6/2.7): guarda contra produção e
`--reset` não duplicando dados.

`pytest-django` força `DEBUG=False` para todos os testes por padrão
(comportamento documentado do plugin, independente do que
`core.settings.local` define) — então o teste da guarda de produção já
exercita o caso real por padrão, e o teste do seed bem-sucedido precisa
reverter isso explicitamente com `override_settings(DEBUG=True)`.
"""

import pytest
from django.core.management import CommandError, call_command
from django.test import override_settings

from apps.decks.infrastructure.mongodb_connection import ensure_mongodb_connection


def _count_documents(collection_name: str) -> int:
    manager = ensure_mongodb_connection()
    collection = manager.get_collection(collection_name)
    return collection.count_documents({})


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_seed_command_refuses_outside_debug():
    with pytest.raises(CommandError):
        call_command("seed_decks")

    assert _count_documents("decks") == 0


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_seed_command_reset_does_not_duplicate():
    call_command("seed_decks")
    first_deck_count = _count_documents("decks")
    first_card_count = _count_documents("cards")

    assert first_deck_count > 0
    assert first_card_count > 0

    call_command("seed_decks", "--reset")

    assert _count_documents("decks") == first_deck_count
    assert _count_documents("cards") == first_card_count
