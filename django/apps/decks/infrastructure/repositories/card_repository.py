"""
Implementação MongoDB do CardRepository

Este módulo implementa a interface ICardRepository usando MongoDB como
banco de dados, via Motor (async). Toda operação de leitura/escrita exige
`owner_id` e embute esse filtro diretamente na query — nunca busca por ID e
confere o dono depois em Python (ver D1 em
openspec/changes/sprint-2-decks-cards/design.md).
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError, OperationFailure
from bson import ObjectId

from apps.decks.domain.entities.card import Card
from apps.decks.domain.repositories.icard_repository import ICardRepository
from apps.decks.infrastructure.exceptions import CardNotFoundError, RepositoryError
from apps.decks.infrastructure.mongodb_connection import ensure_mongodb_connection
from apps.decks.infrastructure.schemas import CardSchema, base_filter, uuid_to_object_id


class CardRepository(ICardRepository):
    """Implementação MongoDB do CardRepository."""

    def __init__(self):
        self._collection_name = "cards"

    async def _get_collection(self) -> AsyncIOMotorCollection:
        # Nunca cacheia a collection na instância: `AsyncIOMotorClient` fica
        # preso ao event loop em que foi criado. Entry points síncronos usam
        # a ponte persistente; seed e testes standalone podem trocar de loop
        # sequencialmente, então a collection continua resolvida por chamada.
        try:
            mongodb_manager = await ensure_mongodb_connection()
            return await mongodb_manager.get_collection(self._collection_name)
        except Exception as e:
            raise RepositoryError(f"Failed to get MongoDB collection: {e}")

    async def save(self, card: Card) -> Card:
        try:
            collection = await self._get_collection()
            card_data = card.to_dict()
            document = CardSchema.to_document(card_data)

            result = await collection.insert_one(document)
            card.id = uuid.UUID(int=int(str(result.inserted_id), 16))

            return card

        except DuplicateKeyError as e:
            raise RepositoryError(f"Card with duplicate key: {e}")
        except Exception as e:
            raise RepositoryError(f"Failed to save card: {e}")

    async def save_many(self, cards: List[Card]) -> List[Card]:
        if not cards:
            return []

        try:
            collection = await self._get_collection()
            documents = [CardSchema.to_document(card.to_dict()) for card in cards]

            result = await collection.insert_many(documents)

            for i, card in enumerate(cards):
                card.id = uuid.UUID(int=int(str(result.inserted_ids[i]), 16))

            return cards

        except Exception as e:
            raise RepositoryError(f"Failed to save cards: {e}")

    async def find_by_id(self, card_id: uuid.UUID, owner_id: str) -> Optional[Card]:
        try:
            collection = await self._get_collection()
            document = await collection.find_one({
                "_id": uuid_to_object_id(card_id),
                **base_filter(owner_id),
            })

            if document is None:
                return None

            card_data = CardSchema.from_document(document)
            return Card.from_dict(card_data)

        except Exception as e:
            raise RepositoryError(f"Failed to find card by ID: {e}")

    async def find_by_front(self, front: str, owner_id: str) -> List[Card]:
        try:
            collection = await self._get_collection()
            front_normalized = front.lower().strip()

            cursor = collection.find({
                "front.normalized": front_normalized,
                **base_filter(owner_id),
            })
            documents = await cursor.to_list(length=None)

            return [Card.from_dict(CardSchema.from_document(doc)) for doc in documents]

        except Exception as e:
            raise RepositoryError(f"Failed to find cards by front: {e}")

    async def find_by_deck_id(self, deck_id: uuid.UUID, owner_id: str) -> List[Card]:
        try:
            collection = await self._get_collection()
            cursor = collection.find({
                "deck_id": uuid_to_object_id(deck_id),
                **base_filter(owner_id),
            })
            documents = await cursor.to_list(length=None)

            return [Card.from_dict(CardSchema.from_document(doc)) for doc in documents]

        except Exception as e:
            raise RepositoryError(f"Failed to find cards by deck ID: {e}")

    async def find_by_context(self, context: str, owner_id: str) -> List[Card]:
        try:
            collection = await self._get_collection()
            cursor = collection.find({"context": context, **base_filter(owner_id)})
            documents = await cursor.to_list(length=None)

            return [Card.from_dict(CardSchema.from_document(doc)) for doc in documents]

        except Exception as e:
            raise RepositoryError(f"Failed to find cards by context: {e}")

    async def find_similar_cards(self, front: str, owner_id: str, similarity_threshold: float = 0.8) -> List[Card]:
        try:
            collection = await self._get_collection()
            front_normalized = front.lower().strip()
            regex_pattern = f".*{front_normalized}.*"

            cursor = collection.find({
                **base_filter(owner_id),
                "$or": [
                    {"front.normalized": {"$regex": regex_pattern, "$options": "i"}},
                    {"back.normalized": {"$regex": regex_pattern, "$options": "i"}}
                ]
            })

            documents = await cursor.to_list(length=None)

            return [Card.from_dict(CardSchema.from_document(doc)) for doc in documents]

        except Exception as e:
            raise RepositoryError(f"Failed to find similar cards: {e}")

    async def find_duplicates(self, card: Card, owner_id: str) -> List[Card]:
        try:
            collection = await self._get_collection()

            exact_matches = await collection.find({
                "front.normalized": card.front.normalized,
                **base_filter(owner_id),
            }).to_list(length=None)

            cards = []
            for document in exact_matches:
                if str(document["_id"]) != str(card.id):
                    cards.append(Card.from_dict(CardSchema.from_document(document)))

            return cards

        except Exception as e:
            raise RepositoryError(f"Failed to find duplicates: {e}")

    async def find_due(self, owner_id: str, due_before: Optional[datetime] = None) -> List[Card]:
        try:
            collection = await self._get_collection()
            due_before = due_before or datetime.now(timezone.utc)

            cursor = collection.find({
                **base_filter(owner_id),
                "due_at": {"$lte": due_before},
            }).sort("due_at", 1)
            documents = await cursor.to_list(length=None)

            return [Card.from_dict(CardSchema.from_document(doc)) for doc in documents]

        except Exception as e:
            raise RepositoryError(f"Failed to find due cards: {e}")

    async def update(self, card: Card) -> Card:
        try:
            collection = await self._get_collection()
            card_data = card.to_dict()
            document = CardSchema.to_document(card_data)
            document.pop("_id", None)

            result = await collection.replace_one(
                {"_id": uuid_to_object_id(card.id), **base_filter(card.owner_id)},
                document
            )

            if result.matched_count == 0:
                raise CardNotFoundError(f"Card with ID {card.id} not found")

            return card

        except CardNotFoundError:
            raise
        except Exception as e:
            raise RepositoryError(f"Failed to update card: {e}")

    async def delete(self, card_id: uuid.UUID, owner_id: str) -> bool:
        """Soft delete (Sprint 6) — marca `deleted_at`, não remove fisicamente."""
        try:
            collection = await self._get_collection()
            now = datetime.now(timezone.utc)

            result = await collection.update_one(
                {"_id": uuid_to_object_id(card_id), **base_filter(owner_id)},
                {"$set": {"deleted_at": now, "updated_at": now}},
            )

            return result.matched_count > 0

        except Exception as e:
            raise RepositoryError(f"Failed to delete card: {e}")

    async def delete_by_deck_id(self, deck_id: uuid.UUID, owner_id: str) -> int:
        """Soft delete de todos os cards do deck (Sprint 6) — cascade a partir de `DeckRepository.delete()`."""
        try:
            collection = await self._get_collection()
            now = datetime.now(timezone.utc)

            result = await collection.update_many(
                {"deck_id": uuid_to_object_id(deck_id), **base_filter(owner_id)},
                {"$set": {"deleted_at": now, "updated_at": now}},
            )

            return result.modified_count

        except Exception as e:
            raise RepositoryError(f"Failed to delete cards by deck ID: {e}")

    async def count(self, owner_id: str) -> int:
        try:
            collection = await self._get_collection()
            return await collection.count_documents(base_filter(owner_id))

        except Exception as e:
            raise RepositoryError(f"Failed to count cards: {e}")

    async def count_by_deck_id(self, deck_id: uuid.UUID, owner_id: str) -> int:
        try:
            collection = await self._get_collection()
            return await collection.count_documents({
                "deck_id": uuid_to_object_id(deck_id),
                **base_filter(owner_id),
            })

        except Exception as e:
            raise RepositoryError(f"Failed to count cards by deck ID: {e}")

    async def exists(self, card_id: uuid.UUID, owner_id: str) -> bool:
        try:
            collection = await self._get_collection()
            count = await collection.count_documents({
                "_id": uuid_to_object_id(card_id),
                **base_filter(owner_id),
            })
            return count > 0

        except Exception as e:
            raise RepositoryError(f"Failed to check if card exists: {e}")

    async def exists_by_front(self, front: str, owner_id: str, deck_id: Optional[uuid.UUID] = None) -> bool:
        try:
            collection = await self._get_collection()
            front_normalized = front.lower().strip()

            query = {"front.normalized": front_normalized, **base_filter(owner_id)}
            if deck_id:
                query["deck_id"] = uuid_to_object_id(deck_id)

            count = await collection.count_documents(query)
            return count > 0

        except Exception as e:
            raise RepositoryError(f"Failed to check if front exists: {e}")

    async def purge_soft_deleted(self, older_than: datetime) -> int:
        """Remove fisicamente cards com `deleted_at` anterior a `older_than` — não escopado por `owner_id` (job de manutenção varre todos os donos)."""
        try:
            collection = await self._get_collection()
            result = await collection.delete_many({"deleted_at": {"$ne": None, "$lt": older_than}})
            return result.deleted_count

        except Exception as e:
            raise RepositoryError(f"Failed to purge soft-deleted cards: {e}")
