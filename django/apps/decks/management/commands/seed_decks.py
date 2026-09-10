"""
Comando de seed multi-tenant para desenvolvimento local (PRD Sprint 2, 2.6).

Entrypoint síncrono, sem event loop (ver `migrate-motor-para-pymongo`:
repositórios rodam sobre `pymongo`, não Motor). Cards são inseridos em lote
via `CardRepository.save_many` (`insert_many` do pymongo) em vez de um loop
`insert_one` por documento — é o volume real do seed (até `CARDS_PER_DECK`
por deck); categorias, decks e reviews são poucos por usuário, inseridos
sequencialmente sem perda de desempenho perceptível.

Uso:
    poetry run python manage.py seed_decks
    poetry run python manage.py seed_decks --reset
"""

import random
from datetime import datetime, timedelta, timezone
from typing import List

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import User
from apps.decks.domain.entities.card import Card
from apps.decks.domain.entities.card_review import CardReview
from apps.decks.domain.entities.category import Category
from apps.decks.domain.entities.deck import Deck
from apps.decks.domain.services import scheduling_service
from apps.decks.domain.value_objects.translation import Translation
from apps.decks.domain.value_objects.word import Word
from apps.decks.infrastructure.mongodb_connection import ensure_mongodb_connection
from apps.decks.infrastructure.repositories.card_repository import CardRepository
from apps.decks.infrastructure.repositories.card_review_repository import (
    CardReviewRepository,
)
from apps.decks.infrastructure.repositories.category_repository import (
    CategoryRepository,
)
from apps.decks.infrastructure.repositories.deck_repository import DeckRepository

SEED_USERNAMES = ["seed_ana", "seed_bruno", "seed_carla"]

# Senha fixa de dev pros usuários seedados — só pra testar o login por
# e-mail/senha (`POST /api/v1/auth/login/`) localmente antes de existirem
# credenciais reais do Google. Documentada em frontend/README.md.
SEED_PASSWORD = "anki12345"

# Título + descrição reais por deck — não um padrão genérico tipo
# "Categoria — Deck N". A Home (Sprint 3) mostra esses valores como
# identificador amigável do "último deck estudado"; um título repetitivo
# não serve pra isso (gap encontrado testando a Home de verdade).
DECK_CATALOG = {
    "Programação": [
        (
            "Estruturas de Dados",
            "Vocabulário essencial sobre arrays, listas encadeadas, pilhas e filas.",
        ),
        (
            "Padrões de Projeto",
            "Termos e conceitos de design patterns usados no dia a dia de desenvolvimento.",
        ),
    ],
    "Viagem": [
        (
            "Aeroporto e Check-in",
            "Frases e vocabulário para embarque, bagagem e check-in em viagens internacionais.",
        ),
        (
            "Hospedagem e Transporte",
            "Vocabulário para reservar hotéis, pedir direções e usar transporte público.",
        ),
    ],
}

CATEGORY_NAMES = list(DECK_CATALOG.keys())

CARDS_PER_DECK = 4

WORD_BANK = [
    ("algorithm", "algoritmo"),
    ("database", "banco de dados"),
    ("keyboard", "teclado"),
    ("network", "rede"),
    ("function", "função"),
    ("variable", "variável"),
    ("compiler", "compilador"),
    ("server", "servidor"),
]

RATINGS = ["again", "hard", "good", "easy"]

# Passado distante, passado recente, e futuro — cobre a variedade de datas
# exigida pelo PRD 2.6 / spec decks-seed-command.
REVIEW_OFFSETS_DAYS = [-14, -3, 5]

SEEDED_COLLECTIONS = ("cards", "decks", "categories", "card_reviews")


class Command(BaseCommand):
    help = "Popula o banco com dados de desenvolvimento multi-tenant (usuários/decks/categorias/cards/reviews)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Remove dados seedados anteriormente (dos usuários de seed) antes de recriar.",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                "seed_decks recusa rodar fora de DEBUG=True (proteção contra produção, ver PRD 2.6)."
            )

        self._run(reset=options["reset"])
        self.stdout.write(self.style.SUCCESS("Seed concluído."))

    def _run(self, reset: bool) -> None:
        ensure_mongodb_connection()

        users = self._get_or_create_seed_users()

        if reset:
            self._reset_seed_data(users)

        for user in users:
            self._seed_for_user(user)

    def _get_or_create_seed_users(self) -> List[User]:
        users = []
        for username in SEED_USERNAMES:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@seed.local"},
            )
            # `get_or_create` não passa por `set_password()` — sem isso
            # o usuário fica com `password=""`. `has_usable_password()`
            # NÃO pega esse caso: ela só verifica o marcador especial de
            # `set_unusable_password()`, e uma string vazia não é esse
            # marcador — `is_password_usable("")` retorna `True`
            # (confirmado lendo o source do Django), então checar só
            # `has_usable_password()` deixaria o seed antigo (sem senha)
            # intocado numa reexecução. Define sempre, incondicional —
            # idempotente, sem custo real de rehash pros 3 usuários.
            user.set_password(SEED_PASSWORD)
            user.save(update_fields=["password"])
            users.append(user)
        return users

    def _reset_seed_data(self, users: List[User]) -> None:
        mongodb_manager = ensure_mongodb_connection()
        owner_ids = [str(user.id) for user in users]

        for collection_name in SEEDED_COLLECTIONS:
            collection = mongodb_manager.get_collection(collection_name)
            collection.delete_many({"owner_id": {"$in": owner_ids}})

    def _seed_for_user(self, user: User) -> None:
        owner_id = str(user.id)

        category_repo = CategoryRepository()
        deck_repo = DeckRepository()
        card_repo = CardRepository()
        review_repo = CardReviewRepository()

        categories = self._create_categories(category_repo, owner_id)
        decks = self._create_decks(deck_repo, owner_id, categories)

        for deck in decks:
            self._seed_deck_cards(card_repo, review_repo, deck, owner_id)

    def _create_categories(
        self, category_repo: CategoryRepository, owner_id: str
    ) -> List[Category]:
        new_categories = [
            Category(name=name, owner_id=owner_id) for name in CATEGORY_NAMES
        ]
        return [category_repo.save(category) for category in new_categories]

    def _create_decks(
        self, deck_repo: DeckRepository, owner_id: str, categories: List[Category]
    ) -> List[Deck]:
        new_decks = [
            Deck(
                title=title,
                description=description,
                owner_id=owner_id,
                category_id=category.id,
            )
            for category in categories
            for title, description in DECK_CATALOG[category.name]
        ]
        return [deck_repo.save(deck) for deck in new_decks]

    def _seed_deck_cards(
        self,
        card_repo: CardRepository,
        review_repo: CardReviewRepository,
        deck: Deck,
        owner_id: str,
    ) -> None:
        deck_tag = deck.title.split(" ")[0].lower()
        sampled_words = random.sample(WORD_BANK, k=CARDS_PER_DECK)
        new_cards = [
            self._build_card(owner_id, deck.id, deck_tag, front, back)
            for front, back in sampled_words
        ]

        cards = card_repo.save_many(new_cards)

        for card in cards:
            self._seed_reviews_for_card(card_repo, review_repo, card, owner_id)

    def _build_card(
        self, owner_id: str, deck_id, tag: str, front: str, back: str
    ) -> Card:
        return Card(
            front=Word(front),
            back=Translation(back),
            front_description=f"This is an example sentence using {front}.",
            back_description=f"Esta é uma frase de exemplo usando {back}.",
            owner_id=owner_id,
            deck_id=deck_id,
            tags=[tag],
        )

    def _seed_reviews_for_card(
        self,
        card_repo: CardRepository,
        review_repo: CardReviewRepository,
        card: Card,
        owner_id: str,
    ) -> None:
        now = datetime.now(timezone.utc)

        for days_offset in REVIEW_OFFSETS_DAYS:
            reviewed_at = now + timedelta(days=days_offset)
            rating = random.choice(RATINGS)

            scheduling_service.review_card(card, rating, reviewed_at=reviewed_at)
            review_repo.save(self._build_review(card, owner_id, rating, reviewed_at))

        card_repo.update(card)

    def _build_review(
        self, card: Card, owner_id: str, rating: str, reviewed_at: datetime
    ) -> CardReview:
        return CardReview(
            card_id=card.id,
            owner_id=owner_id,
            rating=rating,
            reviewed_at=reviewed_at,
            stability_after=card.stability,
            difficulty_after=card.difficulty,
            due_at_after=card.due_at,
            deck_id=card.deck_id,
        )
