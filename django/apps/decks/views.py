"""
Views REST de decks/cards (Sprint 2). Generic Views do DRF sobre
repositórios pymongo (síncronos): serializers puros, `get_queryset()`
devolve uma lista Python já resolvida, nunca um `QuerySet` real (D2/D3 em
openspec/changes/sprint-2-decks-cards/design.md). `APIView` pontual para a
ação de registrar revisão, que não é uma substituição de estado CRUD.
"""

import logging
import uuid

from django.conf import settings
from rest_framework import generics, status
from rest_framework.exceptions import APIException, NotFound, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .domain.entities.card_review import CardReview
from .domain.services import scheduling_service
from .domain.services.export_payload import build_export_payload, compute_content_hash
from .infrastructure import export_records, export_storage
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
from .tasks import export_deck_task

logger = logging.getLogger(__name__)


def _owner_id(request) -> str:
    return str(request.user.id)


class CategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [HasAuthorizedGroup]

    def get_queryset(self):
        return CategoryRepository().find_all(_owner_id(self.request))


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CategorySerializer
    permission_classes = [HasAuthorizedGroup]

    def get_object(self):
        category_id = uuid.UUID(self.kwargs["category_id"])
        category = CategoryRepository().find_by_id(category_id, _owner_id(self.request))
        if category is None:
            raise NotFound()
        return category

    def perform_destroy(self, instance):
        CategoryRepository().delete(instance.id, _owner_id(self.request))


class DeckListCreateView(generics.ListCreateAPIView):
    serializer_class = DeckSerializer
    permission_classes = [HasAuthorizedGroup]

    def get_queryset(self):
        return DeckRepository().find_all(_owner_id(self.request))


class DeckDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DeckSerializer
    permission_classes = [HasAuthorizedGroup]

    def get_object(self):
        deck_id = uuid.UUID(self.kwargs["deck_id"])
        deck = DeckRepository().find_by_id(deck_id, _owner_id(self.request))
        if deck is None:
            raise NotFound()
        return deck

    def perform_destroy(self, instance):
        DeckRepository().delete(instance.id, _owner_id(self.request))


class DeckStatisticsView(APIView):
    """Estatísticas agregadas do histórico ativo de um único deck."""

    permission_classes = [HasAuthorizedGroup]

    def get(self, request, deck_id):
        try:
            parsed_deck_id = uuid.UUID(deck_id)
        except (TypeError, ValueError, AttributeError):
            raise NotFound() from None

        owner_id = _owner_id(request)
        deck = DeckRepository().find_by_id(parsed_deck_id, owner_id)
        if deck is None:
            raise NotFound()

        statistics = CardReviewRepository().get_deck_statistics(
            owner_id,
            parsed_deck_id,
        )
        goal = deck.daily_review_goal
        reviewed_today = statistics["reviewed_today"]
        progress = (
            min(100, round((reviewed_today / goal) * 100)) if goal is not None else None
        )
        return Response(
            {
                **statistics,
                "daily_review_goal": goal,
                "goal_progress_percentage": progress,
            }
        )


class ExportUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Export is temporarily unavailable. Try again shortly."
    default_code = "export_unavailable"


class DeckExportView(APIView):
    """
    `POST /api/v1/decks/{deck_id}/export/` — dispara a exportação `.apkg` de
    forma assíncrona (Sprint 11). Nunca chama o `document-generator` na
    request: só valida, consulta o cache por conteúdo e enfileira a task.

    `202` = geração enfileirada ou já em andamento; `200` = já existe uma
    exportação concluída deste exato conteúdo (cache hit, sem task).
    """

    permission_classes = [HasAuthorizedGroup]

    def post(self, request, deck_id):
        try:
            parsed_deck_id = uuid.UUID(deck_id)
        except (TypeError, ValueError, AttributeError):
            raise NotFound() from None

        owner_id = _owner_id(request)
        deck = DeckRepository().find_by_id(parsed_deck_id, owner_id)
        if deck is None:
            raise NotFound()

        # `find_by_deck_id` só devolve cards ativos (sem `deleted_at`)
        cards = CardRepository().find_by_deck_id(deck.id, owner_id)
        if not cards:
            raise ValidationError({"detail": "This deck has no cards to export."})
        if len(cards) > settings.EXPORT_MAX_CARDS:
            raise ValidationError(
                {
                    "detail": f"A deck export is limited to {settings.EXPORT_MAX_CARDS} cards."
                }
            )

        payload = build_export_payload(deck, cards)
        content_hash = compute_content_hash(payload)
        started = export_records.start_export(owner_id, str(deck.id), content_hash)

        if started.outcome == export_records.ExportOutcome.HIT:
            return Response(
                {"export_id": started.export_id, "status": export_records.COMPLETED},
                status=status.HTTP_200_OK,
            )

        if started.outcome == export_records.ExportOutcome.MISS:
            try:
                export_deck_task.delay(
                    started.export_id, owner_id, str(deck.id), content_hash, payload
                )
            except Exception:
                # sem task, o registro ficaria "pending" travando esse
                # conteúdo até o TTL: libera pra dar pra tentar de novo
                logger.exception("could not enqueue export %s", started.export_id)
                export_records.mark_failed(started.export_id)
                raise ExportUnavailable() from None

        return Response(
            {"export_id": started.export_id, "status": export_records.PENDING},
            status=status.HTTP_202_ACCEPTED,
        )


class DeckExportStatusView(APIView):
    """
    `GET /api/v1/decks/export/{export_id}/status/` — status da exportação
    (Sprint 11, D5/D6). Lê o registro Redis criado no disparo; `404`
    idêntico para id inexistente, expirado ou de outro tenant. Com a
    exportação concluída, devolve uma URL pré-assinada nova a cada chamada
    (assinatura local, nunca guardada).
    """

    permission_classes = [HasAuthorizedGroup]

    def get(self, request, export_id):
        record = export_records.get_record(export_id)
        if record is None or record["owner_id"] != _owner_id(request):
            raise NotFound()

        body = {"export_id": export_id, "status": record["status"]}
        if record["status"] == export_records.COMPLETED:
            body["download_url"] = export_storage.presigned_download_url(
                record["s3_key"]
            )
        return Response(body)


class CardPageNumberPagination(PageNumberPagination):
    page_size = 10


class CardListCreateView(generics.ListCreateAPIView):
    serializer_class = CardSerializer
    permission_classes = [HasAuthorizedGroup]
    pagination_class = CardPageNumberPagination

    def get_queryset(self):
        owner_id = _owner_id(self.request)
        card_repo = CardRepository()
        raw_deck_id = self.request.query_params.get("deck_id")
        deck_id = uuid.UUID(raw_deck_id) if raw_deck_id else None

        if self.request.query_params.get("due") == "true":
            return card_repo.find_due(owner_id, deck_id=deck_id)

        if not deck_id:
            return []

        return card_repo.find_by_deck_id(deck_id, owner_id)


class CardCountView(APIView):
    """Contagem mínima por deck; não materializa documentos de Card."""

    permission_classes = [HasAuthorizedGroup]

    def get(self, request):
        raw_deck_id = request.query_params.get("deck_id")
        try:
            deck_id = uuid.UUID(raw_deck_id) if raw_deck_id else None
        except (TypeError, ValueError, AttributeError):
            deck_id = None

        if deck_id is None:
            raise ValidationError({"deck_id": "Informe um UUID válido."})

        count = CardRepository().count_by_deck_id(
            deck_id,
            _owner_id(request),
        )
        return Response({"count": count})


class CardDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CardSerializer
    permission_classes = [HasAuthorizedGroup]

    def get_object(self):
        card_id = uuid.UUID(self.kwargs["card_id"])
        card = CardRepository().find_by_id(card_id, _owner_id(self.request))
        if card is None:
            raise NotFound()
        return card

    def perform_destroy(self, instance):
        CardRepository().delete(instance.id, _owner_id(self.request))


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

        card = card_repo.find_by_id(uuid.UUID(card_id), owner_id)
        if card is None:
            raise NotFound()

        request_serializer = CardReviewRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        rating = request_serializer.validated_data["rating"]

        scheduling_service.review_card(card, rating)
        card_repo.update(card)

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
        CardReviewRepository().save(review)

        return Response(
            CardReviewSerializer(review).data, status=status.HTTP_201_CREATED
        )


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
        return CardReviewRepository().find_by_owner(_owner_id(self.request))
