import uuid
from typing import List


class Card:
    id: uuid
    word: str
    translation: str
    example: str
    translated_example: str
    context: str


class Deck:
    id: uuid
    title: str
    cards: List[Card]


class AudioRef:
    id: uuid
    card: Card
    path_to_file: str
