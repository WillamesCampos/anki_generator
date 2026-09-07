"""
Implementação MongoDB do CardReviewRepository — um documento por evento de
revisão, owner_id obrigatório (ver D1/D5 em
openspec/changes/sprint-2-decks-cards/design.md).
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
from motor.motor_asyncio import AsyncIOMotorCollection

from apps.decks.domain.entities.card_review import CardReview
from apps.decks.domain.repositories.icard_review_repository import ICardReviewRepository
from apps.decks.infrastructure.exceptions import RepositoryError
from apps.decks.infrastructure.mongodb_connection import ensure_mongodb_connection
from apps.decks.infrastructure.schemas import CardReviewSchema, uuid_to_object_id


class CardReviewRepository(ICardReviewRepository):
    """Implementação MongoDB do CardReviewRepository."""

    def __init__(self):
        self._collection_name = "card_reviews"

    async def _get_collection(self) -> AsyncIOMotorCollection:
        # Nunca cacheia a collection na instância — ver comentário
        # equivalente em CardRepository._get_collection().
        try:
            mongodb_manager = await ensure_mongodb_connection()
            return await mongodb_manager.get_collection(self._collection_name)
        except Exception as e:
            raise RepositoryError(f"Failed to get MongoDB collection: {e}")

    async def save(self, review: CardReview) -> CardReview:
        try:
            collection = await self._get_collection()
            document = CardReviewSchema.to_document(review.to_dict())

            result = await collection.insert_one(document)
            review.id = uuid.UUID(int=int(str(result.inserted_id), 16))

            return review

        except Exception as e:
            raise RepositoryError(f"Failed to save card review: {e}")

    async def find_by_card_id(
        self, card_id: uuid.UUID, owner_id: str
    ) -> List[CardReview]:
        try:
            collection = await self._get_collection()
            cursor = collection.find(
                {
                    "card_id": uuid_to_object_id(card_id),
                    "owner_id": owner_id,
                }
            ).sort("reviewed_at", -1)
            documents = await cursor.to_list(length=None)

            return [
                CardReview.from_dict(CardReviewSchema.from_document(doc))
                for doc in documents
            ]

        except Exception as e:
            raise RepositoryError(f"Failed to find reviews by card ID: {e}")

    async def find_by_owner(self, owner_id: str, limit: int = 100) -> List[CardReview]:
        try:
            collection = await self._get_collection()
            cursor = (
                collection.find({"owner_id": owner_id})
                .sort("reviewed_at", -1)
                .limit(limit)
            )
            documents = await cursor.to_list(length=None)

            return [
                CardReview.from_dict(CardReviewSchema.from_document(doc))
                for doc in documents
            ]

        except Exception as e:
            raise RepositoryError(f"Failed to find reviews by owner: {e}")

    async def get_deck_statistics(
        self, owner_id: str, deck_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Agrega avaliações do histórico ativo sem materializar CardReview.

        O ``$lookup`` restringe a agregação aos cards ainda ativos do mesmo
        owner/deck. O histórico de um card soft-deletado continua preservado,
        mas deixa de participar das estatísticas, conforme a Sprint 6.
        """
        try:
            collection = await self._get_collection()
            deck_object_id = uuid_to_object_id(deck_id)
            today_start = datetime.now(timezone.utc).replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
            pipeline = [
                {
                    "$match": {
                        "owner_id": owner_id,
                        "deck_id": deck_object_id,
                    },
                },
                {
                    "$lookup": {
                        "from": "cards",
                        "let": {"review_card_id": "$card_id"},
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {
                                        "$and": [
                                            {"$eq": ["$_id", "$$review_card_id"]},
                                            {"$eq": ["$owner_id", owner_id]},
                                            {"$eq": ["$deck_id", deck_object_id]},
                                            {"$eq": ["$deleted_at", None]},
                                        ],
                                    },
                                },
                            },
                        ],
                        "as": "active_card",
                    },
                },
                {"$match": {"active_card.0": {"$exists": True}}},
                {
                    "$facet": {
                        "ratings": [
                            {"$group": {"_id": "$rating", "count": {"$sum": 1}}},
                        ],
                        "today": [
                            {"$match": {"reviewed_at": {"$gte": today_start}}},
                            {"$count": "count"},
                        ],
                    },
                },
            ]
            result = await collection.aggregate(pipeline).to_list(length=1)
            facet = result[0] if result else {"ratings": [], "today": []}
            distribution = {"again": 0, "hard": 0, "good": 0, "easy": 0}
            for rating in facet.get("ratings", []):
                if rating["_id"] in distribution:
                    distribution[rating["_id"]] = rating["count"]

            today = facet.get("today", [])
            return {
                "rating_distribution": distribution,
                "reviewed_today": today[0]["count"] if today else 0,
            }

        except Exception as e:
            raise RepositoryError(f"Failed to aggregate deck statistics: {e}")
