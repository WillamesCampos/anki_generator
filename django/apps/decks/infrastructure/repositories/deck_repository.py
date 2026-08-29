"""
Implementação MongoDB do DeckRepository

Este módulo implementa a interface IDeckRepository usando MongoDB como
banco de dados, via Motor (async). Toda operação de leitura/escrita exige
`owner_id` e embute esse filtro diretamente na query (ver D1 em
openspec/changes/sprint-2-decks-cards/design.md).
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError, OperationFailure
from bson import ObjectId

from apps.decks.domain.entities.deck import Deck
from apps.decks.domain.repositories.ideck_repository import IDeckRepository
from apps.decks.infrastructure.exceptions import DeckNotFoundError, RepositoryError
from apps.decks.infrastructure.mongodb_connection import ensure_mongodb_connection
from apps.decks.infrastructure.schemas import DeckSchema, base_filter, uuid_to_object_id


class DeckRepository(IDeckRepository):
    """Implementação MongoDB do DeckRepository."""

    def __init__(self):
        self._collection_name = "decks"

    async def _get_collection(self) -> AsyncIOMotorCollection:
        # Nunca cacheia a collection na instância — ver comentário
        # equivalente em CardRepository._get_collection().
        try:
            mongodb_manager = await ensure_mongodb_connection()
            return await mongodb_manager.get_collection(self._collection_name)
        except Exception as e:
            raise RepositoryError(f"Failed to get MongoDB collection: {e}")

    async def save(self, deck: Deck) -> Deck:
        try:
            collection = await self._get_collection()
            deck_data = deck.to_dict()
            document = DeckSchema.to_document(deck_data)

            result = await collection.insert_one(document)
            deck.id = uuid.UUID(int=int(str(result.inserted_id), 16))

            return deck

        except DuplicateKeyError as e:
            raise RepositoryError(f"Deck with duplicate key: {e}")
        except Exception as e:
            raise RepositoryError(f"Failed to save deck: {e}")

    async def find_by_id(self, deck_id: uuid.UUID, owner_id: str) -> Optional[Deck]:
        try:
            collection = await self._get_collection()
            document = await collection.find_one({
                "_id": uuid_to_object_id(deck_id),
                **base_filter(owner_id),
            })

            if document is None:
                return None

            deck_data = DeckSchema.from_document(document)
            deck = Deck.from_dict(deck_data)

            from apps.decks.infrastructure.repositories.card_repository import CardRepository
            card_repository = CardRepository()
            deck.cards = await card_repository.find_by_deck_id(deck_id, owner_id)

            return deck

        except Exception as e:
            raise RepositoryError(f"Failed to find deck by ID: {e}")

    async def find_by_title(self, title: str, owner_id: str) -> List[Deck]:
        try:
            collection = await self._get_collection()

            cursor = collection.find({
                "title": {"$regex": title, "$options": "i"},
                **base_filter(owner_id),
            })
            documents = await cursor.to_list(length=None)

            return [Deck.from_dict(DeckSchema.from_document(doc)) for doc in documents]

        except Exception as e:
            raise RepositoryError(f"Failed to find decks by title: {e}")

    async def find_all(self, owner_id: str, skip: int = 0, limit: int = 100) -> List[Deck]:
        try:
            collection = await self._get_collection()
            cursor = (
                collection.find(base_filter(owner_id))
                .skip(skip)
                .limit(limit)
                .sort("created_at", -1)
            )
            documents = await cursor.to_list(length=None)

            return [Deck.from_dict(DeckSchema.from_document(doc)) for doc in documents]

        except Exception as e:
            raise RepositoryError(f"Failed to find all decks: {e}")

    async def update(self, deck: Deck) -> Deck:
        try:
            collection = await self._get_collection()
            deck_data = deck.to_dict()
            document = DeckSchema.to_document(deck_data)
            document.pop("_id", None)

            result = await collection.replace_one(
                {"_id": uuid_to_object_id(deck.id), **base_filter(deck.owner_id)},
                document
            )

            if result.matched_count == 0:
                raise DeckNotFoundError(f"Deck with ID {deck.id} not found")

            return deck

        except DeckNotFoundError:
            raise
        except Exception as e:
            raise RepositoryError(f"Failed to update deck: {e}")

    async def delete(self, deck_id: uuid.UUID, owner_id: str) -> bool:
        """Soft delete (Sprint 6) — marca `deleted_at`, cascateia pros cards do deck."""
        try:
            collection = await self._get_collection()
            now = datetime.now(timezone.utc)

            result = await collection.update_one(
                {"_id": uuid_to_object_id(deck_id), **base_filter(owner_id)},
                {"$set": {"deleted_at": now, "updated_at": now}},
            )

            if result.matched_count > 0:
                from apps.decks.infrastructure.repositories.card_repository import CardRepository
                card_repository = CardRepository()
                await card_repository.delete_by_deck_id(deck_id, owner_id)

                return True

            return False

        except Exception as e:
            raise RepositoryError(f"Failed to delete deck: {e}")

    async def unlink_category(self, category_id: uuid.UUID, owner_id: str) -> int:
        """Zera `category_id` em todo deck que referencia essa categoria (Sprint 6, D6) — chamado por `CategoryRepository.delete()`, não cascateia a exclusão do deck em si."""
        try:
            collection = await self._get_collection()
            now = datetime.now(timezone.utc)

            result = await collection.update_many(
                {"category_id": uuid_to_object_id(category_id), "owner_id": owner_id},
                {"$set": {"category_id": None, "updated_at": now}},
            )

            return result.modified_count

        except Exception as e:
            raise RepositoryError(f"Failed to unlink category from decks: {e}")

    async def count(self, owner_id: str) -> int:
        try:
            collection = await self._get_collection()
            return await collection.count_documents(base_filter(owner_id))

        except Exception as e:
            raise RepositoryError(f"Failed to count decks: {e}")

    async def exists(self, deck_id: uuid.UUID, owner_id: str) -> bool:
        try:
            collection = await self._get_collection()
            count = await collection.count_documents({
                "_id": uuid_to_object_id(deck_id),
                **base_filter(owner_id),
            })
            return count > 0

        except Exception as e:
            raise RepositoryError(f"Failed to check if deck exists: {e}")

    async def exists_by_title(self, title: str, owner_id: str) -> bool:
        try:
            collection = await self._get_collection()

            query = {
                "title": {"$regex": f"^{title}$", "$options": "i"},
                **base_filter(owner_id),
            }

            count = await collection.count_documents(query)
            return count > 0

        except Exception as e:
            raise RepositoryError(f"Failed to check if title exists: {e}")

    async def purge_soft_deleted(self, older_than: datetime) -> int:
        """Remove fisicamente decks com `deleted_at` anterior a `older_than` — não escopado por `owner_id` (job de manutenção varre todos os donos)."""
        try:
            collection = await self._get_collection()
            result = await collection.delete_many({"deleted_at": {"$ne": None, "$lt": older_than}})
            return result.deleted_count

        except Exception as e:
            raise RepositoryError(f"Failed to purge soft-deleted decks: {e}")
