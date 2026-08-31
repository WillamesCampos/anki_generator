"""Migração idempotente dos nomes de campos Card anteriores à Sprint 7."""

from django.core.management import call_command

from apps.decks.infrastructure.mongodb_connection import ensure_mongodb_connection

from .conftest import run_async


async def insert_legacy_card():
    manager = await ensure_mongodb_connection()
    collection = await manager.get_collection("cards")
    # Os documentos são limpos entre testes, mas os índices persistem. Restaura
    # explicitamente o estado anterior à migração para que reexecuções da suíte
    # não herdem o índice único de `front.normalized` criado na primeira rodada.
    await collection.drop_indexes()
    await collection.create_index(
        [("deck_id", 1), ("word.normalized", 1)],
        unique=True,
        name="legacy_deck_word",
    )
    result = await collection.insert_one(
        {
            "word": {"value": "network", "normalized": "network"},
            "translation": {
                "value": "rede",
                "normalized": "rede",
                "translations_list": ["rede"],
            },
            "example": {
                "original": "The network is stable.",
                "translated": "A rede está estável.",
            },
        }
    )
    return result.inserted_id


async def insert_intermediate_card():
    manager = await ensure_mongodb_connection()
    collection = await manager.get_collection("cards")
    result = await collection.insert_one(
        {
            "frente": {"value": "database", "normalized": "database"},
            "verso": {
                "value": "banco de dados",
                "normalized": "banco de dados",
                "translations_list": ["banco de dados"],
            },
            "descricao_frente": "The database is stable.",
            "descricao_verso": "O banco de dados está estável.",
        }
    )
    return result.inserted_id


async def read_card(document_id):
    manager = await ensure_mongodb_connection()
    collection = await manager.get_collection("cards")
    return await collection.find_one({"_id": document_id})


async def read_index_fields():
    manager = await ensure_mongodb_connection()
    collection = await manager.get_collection("cards")
    indexes = await collection.list_indexes().to_list(length=None)
    return {field for index in indexes for field in index["key"].keys()}


def test_migrate_card_fields_renames_existing_documents_idempotently():
    legacy_id = run_async(insert_legacy_card())
    intermediate_id = run_async(insert_intermediate_card())

    call_command("migrate_card_fields")
    call_command("migrate_card_fields")
    legacy_document = run_async(read_card(legacy_id))
    intermediate_document = run_async(read_card(intermediate_id))
    index_fields = run_async(read_index_fields())

    assert legacy_document["front"]["value"] == "network"
    assert legacy_document["back"]["value"] == "rede"
    assert legacy_document["front_description"] == "The network is stable."
    assert legacy_document["back_description"] == "A rede está estável."
    assert intermediate_document["front"]["value"] == "database"
    assert intermediate_document["back"]["value"] == "banco de dados"
    assert intermediate_document["front_description"] == "The database is stable."
    assert intermediate_document["back_description"] == "O banco de dados está estável."

    for document in (legacy_document, intermediate_document):
        assert "word" not in document
        assert "translation" not in document
        assert "example" not in document
        assert "frente" not in document
        assert "verso" not in document
        assert "descricao_frente" not in document
        assert "descricao_verso" not in document

    assert "word.normalized" not in index_fields
    assert "frente.normalized" not in index_fields
    assert "front.normalized" in index_fields
