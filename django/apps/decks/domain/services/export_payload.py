"""
Payload de exportação Anki e hash de conteúdo (Sprint 11, D7).

`build_export_payload` monta exatamente o objeto enviado ao
`document-generator`; `compute_content_hash` é calculado **sobre esse mesmo
objeto**. Como só existe um builder, nada exportável pode mudar sem mudar o
hash. Estado FSRS, `owner_id` e timestamps ficam de fora de propósito: não
vão no `.apkg`, então uma revisão de estudo não invalida o cache.
"""

import hashlib
import json
from typing import Iterable

from ..entities.card import Card
from ..entities.deck import Deck

# Sobe quando o formato do pacote muda (template/campos do modelo Anki no
# `document-generator`, ver `EXPORT_FORMAT_VERSION` lá) — invalida todos os
# hashes, e portanto todos os `.apkg` em cache, de uma vez.
EXPORT_FORMAT_VERSION = 1


def build_export_payload(deck: Deck, cards: Iterable[Card]) -> dict:
    """
    Payload de `POST /document-generator/v1/decks/export` a partir do deck e
    dos cards ativos. A ordem dos cards é determinística (`created_at`, depois
    `id`), independente da ordem em que o repositório os devolveu.
    """
    ordered = sorted(cards, key=lambda card: (card.created_at, str(card.id)))
    return {
        "deck_id": str(deck.id),
        "deck_title": deck.title,
        "cards": [
            {
                "id": str(card.id),
                "front": card.front.value,
                "back": card.back.value,
                "front_description": card.front_description,
                "back_description": card.back_description,
            }
            for card in ordered
        ],
    }


def compute_content_hash(payload: dict) -> str:
    """sha256 (hex) do payload serializado de forma canônica + a versão do formato."""
    canonical = json.dumps(
        {"format_version": EXPORT_FORMAT_VERSION, "payload": payload},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
