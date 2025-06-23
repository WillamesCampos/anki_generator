from genanki import Deck
from uuid import uuid4


class DeckGenerator:
    def __init__(self, deck_name: str) -> None:

        self.deck_name = deck_name

    def create_deck(self) -> Deck:
        deck = Deck(
            id=uuid4(),
            name=self.deck_name
        )

        return deck
