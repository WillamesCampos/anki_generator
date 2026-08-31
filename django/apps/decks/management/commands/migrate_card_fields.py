"""Migra documentos Card anteriores ao contrato da Sprint 7."""

from django.core.management.base import BaseCommand

from apps.decks.infrastructure.async_bridge import persistent_async_to_sync
from apps.decks.infrastructure.mongodb_connection import ensure_mongodb_connection


async def migrate_card_fields() -> int:
    manager = await ensure_mongodb_connection()
    collection = await manager.get_collection("cards")
    migrated_ids = set()

    superseded_index_roots = {"word", "translation", "example", "frente", "verso"}
    indexes = await collection.list_indexes().to_list(length=None)
    for index in indexes:
        indexed_fields = index["key"].keys()
        if any(field.split(".", 1)[0] in superseded_index_roots for field in indexed_fields):
            await collection.drop_index(index["name"])

    # A versão intermediária em português tem prioridade sobre o schema
    # legado caso um documento inconsistente contenha os dois. Um campo final
    # já existente nunca é sobrescrito; aliases residuais são removidos.
    renames = (
        ("frente", "front"),
        ("verso", "back"),
        ("descricao_frente", "front_description"),
        ("descricao_verso", "back_description"),
        ("word", "front"),
        ("translation", "back"),
        ("example.original", "front_description"),
        ("example.translated", "back_description"),
    )

    for old_field, new_field in renames:
        query = {
            old_field: {"$exists": True},
            new_field: {"$exists": False},
        }
        documents = await collection.find(query, {"_id": 1}).to_list(length=None)
        migrated_ids.update(document["_id"] for document in documents)
        await collection.update_many(query, {"$rename": {old_field: new_field}})

        duplicate_query = {
            old_field: {"$exists": True},
            new_field: {"$exists": True},
        }
        duplicate_documents = await collection.find(
            duplicate_query,
            {"_id": 1},
        ).to_list(length=None)
        migrated_ids.update(document["_id"] for document in duplicate_documents)
        await collection.update_many(duplicate_query, {"$unset": {old_field: ""}})

    await collection.update_many(
        {
            "$or": [
                {"word": {"$exists": True}},
                {"translation": {"$exists": True}},
                {"example": {"$exists": True}},
            ]
        },
        {"$unset": {"word": "", "translation": "", "example": ""}},
    )
    await manager.create_indexes()
    return len(migrated_ids)


class Command(BaseCommand):
    help = "Migra campos legados/intermediários de Card para o contrato inglês da Sprint 7."

    def handle(self, *args, **options):
        migrated = persistent_async_to_sync(migrate_card_fields)()
        self.stdout.write(self.style.SUCCESS(f"Cards migrados: {migrated}"))
