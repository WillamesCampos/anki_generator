"""
Views REST de decks/cards (Sprint 2). Generic Views do DRF sobre
repositórios Motor: serializers puros, `get_queryset()` devolve uma lista
Python já resolvida via `async_to_sync`, nunca um `QuerySet` real (D2/D3 em
openspec/changes/sprint-2-decks-cards/design.md). `APIView` pontual para a
ação de registrar revisão, que não é uma substituição de estado CRUD.
"""

import uuid

from asgiref.sync import async_to_sync
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from .domain.entities.card_review import CardReview
from .domain.services import scheduling_service
from .infrastructure.repositories.card_repository import CardRepository
from .infrastructure.repositories.card_review_repository import CardReviewRepository
from .infrastructure.repositories.category_repository import CategoryRepository
from .infrastructure.repositories.deck_repository import DeckRepository
from .permissions import HasAuthorizedGroup
from .serializers import (
    CardReviewRequestSerializer,
    CardReviewSerializer,
    CardSerializer,
    CategorySerializer,
    DeckSerializer,
)


def _owner_id(request) -> str:
    return str(request.user.id)


class CategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [HasAuthorizedGroup]

    def get_queryset(self):
        return async_to_sync(CategoryRepository().find_all)(_owner_id(self.request))


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CategorySerializer
    permission_classes = [HasAuthorizedGroup]

    def get_object(self):
        category_id = uuid.UUID(self.kwargs["category_id"])
        category = async_to_sync(CategoryRepository().find_by_id)(category_id, _owner_id(self.request))
        if category is None:
            raise NotFound()
        return category

    def perform_destroy(self, instance):
        async_to_sync(CategoryRepository().delete)(instance.id, _owner_id(self.request))


class DeckListCreateView(generics.ListCreateAPIView):
    serializer_class = DeckSerializer
    permission_classes = [HasAuthorizedGroup]

    def get_queryset(self):
        return async_to_sync(DeckRepository().find_all)(_owner_id(self.request))


class DeckDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DeckSerializer
    permission_classes = [HasAuthorizedGroup]

    def get_object(self):
        deck_id = uuid.UUID(self.kwargs["deck_id"])
        deck = async_to_sync(DeckRepository().find_by_id)(deck_id, _owner_id(self.request))
        if deck is None:
            raise NotFound()
        return deck

    def perform_destroy(self, instance):
        async_to_sync(DeckRepository().delete)(instance.id, _owner_id(self.request))


class CardListCreateView(generics.ListCreateAPIView):
    serializer_class = CardSerializer
    permission_classes = [HasAuthorizedGroup]

    def get_queryset(self):
        owner_id = _owner_id(self.request)
        card_repo = CardRepository()

        if self.request.query_params.get("due") == "true":
            return async_to_sync(card_repo.find_due)(owner_id)

        deck_id = self.request.query_params.get("deck_id")
        if not deck_id:
            return []

        return async_to_sync(card_repo.find_by_deck_id)(uuid.UUID(deck_id), owner_id)


class CardDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CardSerializer
    permission_classes = [HasAuthorizedGroup]

    def get_object(self):
        card_id = uuid.UUID(self.kwargs["card_id"])
        card = async_to_sync(CardRepository().find_by_id)(card_id, _owner_id(self.request))
        if card is None:
            raise NotFound()
        return card

    def perform_destroy(self, instance):
        async_to_sync(CardRepository().delete)(instance.id, _owner_id(self.request))


class CardReviewView(APIView):
    """
    `POST /api/v1/cards/{card_id}/review/` — dispara o agendamento FSRS
    (domain/services/scheduling_service.py) e grava o evento em
    `CardReview` (D4/D5 em design.md). Ação de domínio, não CRUD, por isso
    `APIView` em vez de um Generic View (D2).
    """

    permission_classes = [HasAuthorizedGroup]

    def post(self, request, card_id):
        owner_id = _owner_id(request)
        card_repo = CardRepository()

        card = async_to_sync(card_repo.find_by_id)(uuid.UUID(card_id), owner_id)
        if card is None:
            raise NotFound()

        request_serializer = CardReviewRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        rating = request_serializer.validated_data["rating"]

        scheduling_service.review_card(card, rating)
        async_to_sync(card_repo.update)(card)

        review = CardReview(
            card_id=card.id,
            owner_id=owner_id,
            rating=rating,
            stability_after=card.stability,
            difficulty_after=card.difficulty,
            due_at_after=card.due_at,
            deck_id=card.deck_id,
            created_by=owner_id,
            updated_by=owner_id,
        )
        async_to_sync(CardReviewRepository().save)(review)

        return Response(CardReviewSerializer(review).data, status=status.HTTP_201_CREATED)


class CardReviewListView(generics.ListAPIView):
    """
    `GET /api/v1/reviews/` — histórico de revisões do usuário, mais
    recentes primeiro. Adicionado na Sprint 3 (Home dashboard: último deck
    estudado, gráfico de estatísticas) — gap encontrado em implementação,
    já que a Sprint 2 só persistia `CardReview`, sem endpoint de leitura.
    """

    serializer_class = CardReviewSerializer
    permission_classes = [HasAuthorizedGroup]

    def get_queryset(self):
        return async_to_sync(CardReviewRepository().find_by_owner)(_owner_id(self.request))
