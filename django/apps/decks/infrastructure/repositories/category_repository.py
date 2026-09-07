"""
Implementação MongoDB do CategoryRepository — mesmo padrão de owner_id
obrigatório dos demais repositórios (ver D1/D6 em
openspec/changes/sprint-2-decks-cards/design.md).
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection

from apps.decks.domain.entities.category import Category
from apps.decks.domain.repositories.icategory_repository import ICategoryRepository
from apps.decks.infrastructure.exceptions import CategoryNotFoundError, RepositoryError
from apps.decks.infrastructure.mongodb_connection import ensure_mongodb_connection
from apps.decks.infrastructure.schemas import (
    CategorySchema,
    base_filter,
    uuid_to_object_id,
)


class CategoryRepository(ICategoryRepository):
    """Implementação MongoDB do CategoryRepository."""

    def __init__(self):
        self._collection_name = "categories"

    async def _get_collection(self) -> AsyncIOMotorCollection:
        # Nunca cacheia a collection na instância — ver comentário
        # equivalente em CardRepository._get_collection().
        try:
            mongodb_manager = await ensure_mongodb_connection()
            return await mongodb_manager.get_collection(self._collection_name)
        except Exception as e:
            raise RepositoryError(f"Failed to get MongoDB collection: {e}")

    async def save(self, category: Category) -> Category:
        try:
            collection = await self._get_collection()
            document = CategorySchema.to_document(category.to_dict())

            result = await collection.insert_one(document)
            category.id = uuid.UUID(int=int(str(result.inserted_id), 16))

            return category

        except Exception as e:
            raise RepositoryError(f"Failed to save category: {e}")

    async def find_by_id(
        self, category_id: uuid.UUID, owner_id: str
    ) -> Optional[Category]:
        try:
            collection = await self._get_collection()
            document = await collection.find_one(
                {
                    "_id": uuid_to_object_id(category_id),
                    **base_filter(owner_id),
                }
            )

            if document is None:
                return None

            return Category.from_dict(CategorySchema.from_document(document))

        except Exception as e:
            raise RepositoryError(f"Failed to find category by ID: {e}")

    async def find_all(self, owner_id: str) -> List[Category]:
        try:
            collection = await self._get_collection()
            cursor = collection.find(base_filter(owner_id)).sort("name", 1)
            documents = await cursor.to_list(length=None)

            return [
                Category.from_dict(CategorySchema.from_document(doc))
                for doc in documents
            ]

        except Exception as e:
            raise RepositoryError(f"Failed to find categories: {e}")

    async def update(self, category: Category) -> Category:
        try:
            collection = await self._get_collection()
            document = CategorySchema.to_document(category.to_dict())
            document.pop("_id", None)

            result = await collection.replace_one(
                {
                    "_id": uuid_to_object_id(category.id),
                    **base_filter(category.owner_id),
                },
                document,
            )

            if result.matched_count == 0:
                raise CategoryNotFoundError(f"Category with ID {category.id} not found")

            return category

        except CategoryNotFoundError:
            raise
        except Exception as e:
            raise RepositoryError(f"Failed to update category: {e}")

    async def delete(self, category_id: uuid.UUID, owner_id: str) -> bool:
        """Soft delete (Sprint 6) — marca `deleted_at` e desvincula (não cascateia) os decks que a referenciam (ver D6 em design.md)."""
        try:
            collection = await self._get_collection()
            now = datetime.now(timezone.utc)

            result = await collection.update_one(
                {"_id": uuid_to_object_id(category_id), **base_filter(owner_id)},
                {"$set": {"deleted_at": now, "updated_at": now}},
            )

            if result.matched_count > 0:
                from apps.decks.infrastructure.repositories.deck_repository import (
                    DeckRepository,
                )

                deck_repository = DeckRepository()
                await deck_repository.unlink_category(category_id, owner_id)

                return True

            return False

        except Exception as e:
            raise RepositoryError(f"Failed to delete category: {e}")

    async def exists(self, category_id: uuid.UUID, owner_id: str) -> bool:
        try:
            collection = await self._get_collection()
            count = await collection.count_documents(
                {
                    "_id": uuid_to_object_id(category_id),
                    **base_filter(owner_id),
                }
            )
            return count > 0

        except Exception as e:
            raise RepositoryError(f"Failed to check if category exists: {e}")

    async def purge_soft_deleted(self, older_than: datetime) -> int:
        """Remove fisicamente categorias com `deleted_at` anterior a `older_than` — não escopado por `owner_id` (job de manutenção varre todos os donos)."""
        try:
            collection = await self._get_collection()
            result = await collection.delete_many(
                {"deleted_at": {"$ne": None, "$lt": older_than}}
            )
            return result.deleted_count

        except Exception as e:
            raise RepositoryError(f"Failed to purge soft-deleted categories: {e}")
