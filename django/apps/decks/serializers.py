"""
Serializers do domínio de decks/cards — todos `serializers.Serializer`
puros, nunca `ModelSerializer` (que exige um Django Model real): o dado
vive em MongoDB via repositórios pymongo (síncronos), não no ORM (ver D2 em
openspec/changes/sprint-2-decks-cards/design.md). `create()`/`update()`
delegam diretamente ao repositório correspondente (D3/D9).

`owner_id` nunca é aceito como input do cliente — sempre vem de
`self.context["request"].user`, no mesmo espírito do `AuditSerializerMixin`
da Sprint 1 (apps/accounts/audit.py).
"""

from datetime import datetime, timezone

from rest_framework import serializers

from .domain.entities.card import Card
from .domain.entities.card_review import VALID_RATINGS
from .domain.entities.category import Category
from .domain.entities.deck import Deck
from .domain.value_objects.translation import Translation
from .domain.value_objects.word import Word
from .infrastructure.repositories.card_repository import CardRepository
from .infrastructure.repositories.category_repository import CategoryRepository
from .infrastructure.repositories.deck_repository import DeckRepository


class CategorySerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=200)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def create(self, validated_data):
        owner_id = str(self.context["request"].user.id)
        category = Category(
            name=validated_data["name"],
            owner_id=owner_id,
            created_by=owner_id,
            updated_by=owner_id,
        )
        return CategoryRepository().save(category)

    def update(self, instance: Category, validated_data):
        if "name" in validated_data:
            instance.rename(validated_data["name"])
        instance.updated_by = str(self.context["request"].user.id)
        return CategoryRepository().update(instance)


class DeckSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(allow_blank=True, required=False, default="")
    category_id = serializers.UUIDField(required=False, allow_null=True)
    max_cards_per_generation = serializers.IntegerField(required=False, default=10)
    daily_review_goal = serializers.IntegerField(
        required=False, allow_null=True, min_value=1
    )
    card_count = serializers.IntegerField(read_only=True)
    is_empty = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def create(self, validated_data):
        owner_id = str(self.context["request"].user.id)
        deck = Deck(
            title=validated_data["title"],
            owner_id=owner_id,
            description=validated_data.get("description", ""),
            category_id=validated_data.get("category_id"),
            max_cards_per_generation=validated_data.get("max_cards_per_generation", 10),
            daily_review_goal=validated_data.get("daily_review_goal"),
            created_by=owner_id,
            updated_by=owner_id,
        )
        return DeckRepository().save(deck)

    def update(self, instance: Deck, validated_data):
        if "title" in validated_data:
            instance.update_title(validated_data["title"])
        if "description" in validated_data:
            instance.update_description(validated_data["description"])
        if "category_id" in validated_data:
            instance.category_id = validated_data["category_id"]
            instance.updated_at = datetime.now(timezone.utc)
        if "daily_review_goal" in validated_data:
            instance.update_daily_review_goal(validated_data["daily_review_goal"])
        instance.updated_by = str(self.context["request"].user.id)
        return DeckRepository().update(instance)


class CardSerializer(serializers.Serializer):
    """
    `front`/`back`/`front_description`/`back_description` são campos
    de entrada planos — o Card real guarda objetos de valor (`Word`,
    `Translation`), por isso a representação de saída é montada
    manualmente em `to_representation`, em vez de depender do mapeamento
    automático de atributo do DRF.
    """

    id = serializers.UUIDField(read_only=True)
    front = serializers.CharField(max_length=200)
    back = serializers.CharField(max_length=200)
    front_description = serializers.CharField()
    back_description = serializers.CharField()
    context = serializers.CharField(allow_blank=True, required=False, default="")
    deck_id = serializers.UUIDField()
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50), required=False, default=list
    )

    def to_representation(self, instance: Card) -> dict:
        return {
            "id": str(instance.id),
            "front": instance.front.value,
            "back": instance.back.value,
            "front_description": instance.front_description,
            "back_description": instance.back_description,
            "context": instance.context,
            "deck_id": str(instance.deck_id) if instance.deck_id else None,
            "tags": list(instance.tags),
            "fsrs_state": instance.fsrs_state,
            "stability": instance.stability,
            "difficulty": instance.difficulty,
            "due_at": instance.due_at.isoformat(),
            "last_reviewed_at": (
                instance.last_reviewed_at.isoformat()
                if instance.last_reviewed_at
                else None
            ),
            "created_at": instance.created_at.isoformat(),
            "updated_at": instance.updated_at.isoformat(),
        }

    def create(self, validated_data):
        owner_id = str(self.context["request"].user.id)
        card = Card(
            front=Word(validated_data["front"]),
            back=Translation(validated_data["back"]),
            front_description=validated_data["front_description"],
            back_description=validated_data["back_description"],
            owner_id=owner_id,
            context=validated_data.get("context", ""),
            deck_id=validated_data["deck_id"],
            tags=list(validated_data.get("tags", [])),
            created_by=owner_id,
            updated_by=owner_id,
        )
        return CardRepository().save(card)

    def update(self, instance: Card, validated_data):
        if "front" in validated_data:
            instance.front = Word(validated_data["front"])
        if "back" in validated_data:
            new_back = Translation(validated_data["back"])
            if new_back != instance.back:
                instance.update_back(new_back)
        if (
            "front_description" in validated_data
            or "back_description" in validated_data
        ):
            instance.update_descriptions(
                validated_data.get("front_description", instance.front_description),
                validated_data.get("back_description", instance.back_description),
            )
        if "context" in validated_data:
            instance.context = validated_data["context"]
        if "tags" in validated_data:
            instance.tags = list(validated_data["tags"])
        instance.updated_at = datetime.now(timezone.utc)
        instance.updated_by = str(self.context["request"].user.id)
        return CardRepository().update(instance)


class CardReviewRequestSerializer(serializers.Serializer):
    """Body de `POST /api/v1/cards/{id}/review/`."""

    rating = serializers.ChoiceField(choices=sorted(VALID_RATINGS))


class CardReviewSerializer(serializers.Serializer):
    """Representação de saída de um `CardReview` já persistido."""

    def to_representation(self, instance) -> dict:
        return instance.to_dict()
