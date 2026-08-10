"""
URLs do domínio de decks/cards. Versionamento (`/api/v1/`) é aplicado uma
única vez em `core/urls.py`, no `include()` deste módulo — mesmo padrão do
`API_PREFIX` usado nos microsserviços FastAPI (ver
`<regra_obrigatoria id="versionamento-url-microservicos">` em
PROMPT_REFINADO.md).
"""

from django.urls import path

from . import views

urlpatterns = [
    path("categories/", views.CategoryListCreateView.as_view(), name="category-list"),
    path("categories/<str:category_id>/", views.CategoryDetailView.as_view(), name="category-detail"),
    path("decks/", views.DeckListCreateView.as_view(), name="deck-list"),
    path("decks/<str:deck_id>/", views.DeckDetailView.as_view(), name="deck-detail"),
    path("cards/", views.CardListCreateView.as_view(), name="card-list"),
    path("cards/<str:card_id>/", views.CardDetailView.as_view(), name="card-detail"),
    path("cards/<str:card_id>/review/", views.CardReviewView.as_view(), name="card-review"),
]
