"""
Schemas MongoDB para o Sistema de Geração de Cards Anki

Este módulo define os schemas (estruturas de dados) para as collections
do MongoDB. Os schemas garantem consistência e validação dos dados
armazenados.

Collections definidas:
- cards: Cards individuais do Anki
- decks: Coleções de cards
- generation_sessions: Sessões de geração de cards
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from bson import ObjectId


def datetime_from_mongo(value: datetime) -> str:
    """
    Converte um datetime lido do MongoDB para string ISO, sempre com o
    offset UTC explícito.

    Pymongo/Motor devolvem datetimes *naive* na leitura (mesmo quando o
    valor foi inserido como aware) — sem esse `replace`, o `.isoformat()`
    resultante não carrega offset, e `datetime.fromisoformat()` do lado do
    domínio reconstrói um datetime naive de novo. Isso já causou um bug
    real: revisar o mesmo card uma segunda vez (com `last_reviewed_at`
    vindo do Mongo) quebrava com "can't subtract offset-naive and
    offset-aware datetimes" dentro do `fsrs.Scheduler`. Toda leitura de
    datetime do Mongo passa por aqui.
    """
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def uuid_to_object_id(value) -> ObjectId:
    """
    Converte de volta para ObjectId um identificador que veio de
    `uuid.UUID(int=int(<objectid_hex>, 16))` (ver repositories/*.py `save()`)
    — os 96 bits baixos do UUID resultante são exatamente o ObjectId original.
    Também aceita um ObjectId (devolvido sem alteração) ou uma string de
    ObjectId de 24 chars, por compatibilidade.
    """
    if isinstance(value, ObjectId):
        return value

    hex_str = str(value).replace("-", "")
    if len(hex_str) == 32:
        hex_str = hex_str[-24:]

    return ObjectId(hex_str)


class MongoDBSchema:
    """
    Classe base para schemas MongoDB.

    Fornece métodos utilitários para conversão entre
    entidades de domínio e documentos MongoDB.
    """

    @staticmethod
    def to_object_id(id_value: str) -> ObjectId:
        """
        Converte string ID para ObjectId MongoDB.

        Args:
            id_value: ID como string

        Returns:
            ObjectId MongoDB
        """
        if isinstance(id_value, ObjectId):
            return id_value
        return ObjectId(id_value)

    @staticmethod
    def to_string_id(object_id: ObjectId) -> str:
        """
        Converte ObjectId para a string de UUID usada pelas entidades de
        domínio (`Card.id`, `Deck.id`, `GenerationSession.id`) — o inverso de
        `uuid_to_object_id`. NÃO usar `str(object_id)` puro aqui: o hex do
        ObjectId (24 chars) não é um UUID válido (precisa de 32).

        Args:
            object_id: ObjectId MongoDB

        Returns:
            ID como string de UUID
        """
        import uuid

        return str(uuid.UUID(int=int(str(object_id), 16)))


class CardSchema(MongoDBSchema):
    """
    Schema para collection 'cards'.

    Estrutura do documento:
    {
        "_id": ObjectId,
        "word": {
            "value": string,
            "normalized": string
        },
        "translation": {
            "value": string,
            "normalized": string,
            "translations_list": [string]
        },
        "example": {
            "original": string,
            "translated": string,
            "original_normalized": string,
            "translated_normalized": string
        },
        "audio_path": {
            "path": string,
            "filename": string,
            "exists": boolean
        } | null,
        "context": string,
        "deck_id": ObjectId,
        "created_at": datetime,
        "updated_at": datetime
    }
    """

    @staticmethod
    def to_document(card_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converte dados de card para documento MongoDB.

        Args:
            card_data: Dados do card (vindos de card.to_dict())

        Returns:
            Documento MongoDB
        """
        document = {
            "_id": ObjectId(),  # Gera um novo ObjectId
            "word": {
                "value": card_data["word"]["value"],
                "normalized": card_data["word"]["normalized"]
            },
            "translation": {
                "value": card_data["translation"]["value"],
                "normalized": card_data["translation"]["normalized"],
                "translations_list": card_data["translation"]["translations_list"]
            },
            "example": {
                "original": card_data["example"]["original"],
                "translated": card_data["example"]["translated"],
                "original_normalized": card_data["example"]["original_normalized"],
                "translated_normalized": card_data["example"]["translated_normalized"]
            },
            "owner_id": card_data["owner_id"],
            "context": card_data["context"],
            "deck_id": uuid_to_object_id(card_data["deck_id"]) if card_data["deck_id"] else None,
            "tags": list(card_data.get("tags", [])),
            "fsrs_state": card_data.get("fsrs_state", 1),
            "fsrs_step": card_data.get("fsrs_step"),
            "stability": card_data.get("stability"),
            "difficulty": card_data.get("difficulty"),
            "due_at": datetime.fromisoformat(card_data["due_at"]),
            "last_reviewed_at": (
                datetime.fromisoformat(card_data["last_reviewed_at"])
                if card_data.get("last_reviewed_at") else None
            ),
            "created_at": datetime.fromisoformat(card_data["created_at"]),
            "updated_at": datetime.fromisoformat(card_data["updated_at"])
        }

        # Adiciona audio_path se existir
        if card_data.get("audio_path"):
            document["audio_path"] = {
                "path": card_data["audio_path"]["path"],
                "filename": card_data["audio_path"]["filename"],
                "exists": card_data["audio_path"]["exists"]
            }

        return document

    @staticmethod
    def from_document(document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converte documento MongoDB para dados de card.

        Args:
            document: Documento MongoDB

        Returns:
            Dados do card (para card.from_dict())
        """
        card_data = {
            "id": CardSchema.to_string_id(document["_id"]),
            "word": {
                "value": document["word"]["value"],
                "normalized": document["word"]["normalized"],
                "length": len(document["word"]["value"]),
                "word_count": len(document["word"]["value"].split())
            },
            "translation": {
                "value": document["translation"]["value"],
                "normalized": document["translation"]["normalized"],
                "translations_list": document["translation"]["translations_list"],
                "primary_translation": document["translation"]["translations_list"][0] if document["translation"]["translations_list"] else document["translation"]["value"],
                "alternative_translations": document["translation"]["translations_list"][1:] if len(document["translation"]["translations_list"]) > 1 else [],
                "translation_count": len(document["translation"]["translations_list"])
            },
            "example": {
                "original": document["example"]["original"],
                "translated": document["example"]["translated"],
                "original_normalized": document["example"]["original_normalized"],
                "translated_normalized": document["example"]["translated_normalized"],
                "word_count_original": len(document["example"]["original"].split()),
                "word_count_translated": len(document["example"]["translated"].split()),
                "length_original": len(document["example"]["original"]),
                "length_translated": len(document["example"]["translated"])
            },
            "owner_id": document["owner_id"],
            "context": document["context"],
            "deck_id": CardSchema.to_string_id(document["deck_id"]) if document["deck_id"] else None,
            "tags": list(document.get("tags", [])),
            "fsrs_state": document.get("fsrs_state", 1),
            "fsrs_step": document.get("fsrs_step"),
            "stability": document.get("stability"),
            "difficulty": document.get("difficulty"),
            "due_at": datetime_from_mongo(document["due_at"]),
            "last_reviewed_at": datetime_from_mongo(document["last_reviewed_at"]) if document.get("last_reviewed_at") else None,
            "created_at": datetime_from_mongo(document["created_at"]),
            "updated_at": datetime_from_mongo(document["updated_at"])
        }

        # Adiciona audio_path se existir
        if document.get("audio_path"):
            card_data["audio_path"] = {
                "path": document["audio_path"]["path"],
                "filename": document["audio_path"]["filename"],
                "directory": document["audio_path"]["path"].rsplit('/', 1)[0] if '/' in document["audio_path"]["path"] else "",
                "extension": document["audio_path"]["path"].split('.')[-1] if '.' in document["audio_path"]["path"] else "",
                "stem": document["audio_path"]["filename"].rsplit('.', 1)[0] if '.' in document["audio_path"]["filename"] else document["audio_path"]["filename"],
                "exists": document["audio_path"]["exists"],
                "size_bytes": None  # Seria necessário verificar o arquivo
            }

        return card_data


class DeckSchema(MongoDBSchema):
    """
    Schema para collection 'decks'.

    Estrutura do documento:
    {
        "_id": ObjectId,
        "title": string,
        "description": string,
        "max_cards_per_generation": int,
        "created_at": datetime,
        "updated_at": datetime,
        "card_count": int,
        "is_empty": boolean
    }
    """

    @staticmethod
    def to_document(deck_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converte dados de deck para documento MongoDB.

        Args:
            deck_data: Dados do deck (vindos de deck.to_dict())

        Returns:
            Documento MongoDB
        """
        return {
            "_id": ObjectId(),  # Gera um novo ObjectId
            "title": deck_data["title"],
            "owner_id": deck_data["owner_id"],
            "description": deck_data["description"],
            "category_id": uuid_to_object_id(deck_data["category_id"]) if deck_data.get("category_id") else None,
            "max_cards_per_generation": deck_data["max_cards_per_generation"],
            "created_at": datetime.fromisoformat(deck_data["created_at"]),
            "updated_at": datetime.fromisoformat(deck_data["updated_at"]),
            "card_count": deck_data["card_count"],
            "is_empty": deck_data["is_empty"]
        }

    @staticmethod
    def from_document(document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converte documento MongoDB para dados de deck.

        Args:
            document: Documento MongoDB

        Returns:
            Dados do deck (para deck.from_dict())
        """
        return {
            "id": DeckSchema.to_string_id(document["_id"]),
            "title": document["title"],
            "owner_id": document["owner_id"],
            "description": document["description"],
            "category_id": DeckSchema.to_string_id(document["category_id"]) if document.get("category_id") else None,
            "cards": [],  # Cards são carregados separadamente
            "max_cards_per_generation": document["max_cards_per_generation"],
            "created_at": datetime_from_mongo(document["created_at"]),
            "updated_at": datetime_from_mongo(document["updated_at"]),
            "card_count": document["card_count"],
            "is_empty": document["is_empty"]
        }


class CategorySchema(MongoDBSchema):
    """
    Schema para collection 'categories'.

    {
        "_id": ObjectId,
        "name": string,
        "owner_id": string,
        "created_at": datetime,
        "updated_at": datetime
    }
    """

    @staticmethod
    def to_document(category_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "_id": ObjectId(),
            "name": category_data["name"],
            "owner_id": category_data["owner_id"],
            "created_at": datetime.fromisoformat(category_data["created_at"]),
            "updated_at": datetime.fromisoformat(category_data["updated_at"]),
        }

    @staticmethod
    def from_document(document: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": CategorySchema.to_string_id(document["_id"]),
            "name": document["name"],
            "owner_id": document["owner_id"],
            "created_at": datetime_from_mongo(document["created_at"]),
            "updated_at": datetime_from_mongo(document["updated_at"]),
        }


class CardReviewSchema(MongoDBSchema):
    """
    Schema para collection 'card_reviews' — um documento por evento de
    revisão (ver D5 em openspec/changes/sprint-2-decks-cards/design.md).

    {
        "_id": ObjectId,
        "card_id": ObjectId,
        "owner_id": string,
        "rating": string,
        "reviewed_at": datetime,
        "stability_after": float | null,
        "difficulty_after": float | null,
        "due_at_after": datetime | null,
        "deck_id": ObjectId | null
    }
    """

    @staticmethod
    def to_document(review_data: Dict[str, Any]) -> Dict[str, Any]:
        document = {
            "_id": ObjectId(),
            "card_id": uuid_to_object_id(review_data["card_id"]),
            "owner_id": review_data["owner_id"],
            "rating": review_data["rating"],
            "reviewed_at": datetime.fromisoformat(review_data["reviewed_at"]),
            "stability_after": review_data.get("stability_after"),
            "difficulty_after": review_data.get("difficulty_after"),
            "deck_id": uuid_to_object_id(review_data["deck_id"]) if review_data.get("deck_id") else None,
        }

        if review_data.get("due_at_after"):
            document["due_at_after"] = datetime.fromisoformat(review_data["due_at_after"])

        return document

    @staticmethod
    def from_document(document: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": CardReviewSchema.to_string_id(document["_id"]),
            "card_id": CardReviewSchema.to_string_id(document["card_id"]),
            "owner_id": document["owner_id"],
            "rating": document["rating"],
            "reviewed_at": datetime_from_mongo(document["reviewed_at"]),
            "stability_after": document.get("stability_after"),
            "difficulty_after": document.get("difficulty_after"),
            "due_at_after": datetime_from_mongo(document["due_at_after"]) if document.get("due_at_after") else None,
            "deck_id": CardReviewSchema.to_string_id(document["deck_id"]) if document.get("deck_id") else None,
        }


class GenerationSessionSchema(MongoDBSchema):
    """
    Schema para collection 'generation_sessions'.

    Estrutura do documento:
    {
        "_id": ObjectId,
        "context": string,
        "deck_id": ObjectId,
        "status": string,
        "max_cards": int,
        "created_at": datetime,
        "updated_at": datetime,
        "completed_at": datetime | null,
        "error_message": string | null,
        "cards_generated_count": int,
        "is_finished": boolean
    }
    """

    @staticmethod
    def to_document(session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converte dados de sessão para documento MongoDB.

        Args:
            session_data: Dados da sessão (vindos de session.to_dict())

        Returns:
            Documento MongoDB
        """
        document = {
            "_id": ObjectId(),  # Gera um novo ObjectId
            "context": session_data["context"],
            "deck_id": uuid_to_object_id(session_data["deck_id"]) if session_data["deck_id"] else None,
            "status": session_data["status"],
            "max_cards": session_data["max_cards"],
            "created_at": datetime.fromisoformat(session_data["created_at"]),
            "updated_at": datetime.fromisoformat(session_data["updated_at"]),
            "cards_generated_count": session_data["cards_generated_count"],
            "is_finished": session_data["is_finished"]
        }

        # Adiciona campos opcionais
        if session_data.get("completed_at"):
            document["completed_at"] = datetime.fromisoformat(session_data["completed_at"])

        if session_data.get("error_message"):
            document["error_message"] = session_data["error_message"]

        return document

    @staticmethod
    def from_document(document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converte documento MongoDB para dados de sessão.

        Args:
            document: Documento MongoDB

        Returns:
            Dados da sessão (para session.from_dict())
        """
        session_data = {
            "id": GenerationSessionSchema.to_string_id(document["_id"]),
            "context": document["context"],
            "deck_id": GenerationSessionSchema.to_string_id(document["deck_id"]),
            "status": document["status"],
            "generated_cards": [],  # Cards são carregados separadamente
            "max_cards": document["max_cards"],
            "created_at": datetime_from_mongo(document["created_at"]),
            "updated_at": datetime_from_mongo(document["updated_at"]),
            "cards_generated_count": document["cards_generated_count"],
            "is_finished": document["is_finished"]
        }

        # Adiciona campos opcionais
        if document.get("completed_at"):
            session_data["completed_at"] = datetime_from_mongo(document["completed_at"])

        if document.get("error_message"):
            session_data["error_message"] = document["error_message"]

        return session_data


class IndexDefinitions:
    """
    Definições de índices para otimização das consultas MongoDB.
    """

    # Índices para collection cards
    CARDS_INDEXES = [
        ("owner_id", 1),
        ("deck_id", 1),
        ("word.normalized", 1),
        ("created_at", 1),
        ("updated_at", 1),
        ("context", 1),
        ("due_at", 1),
        ("tags", 1),
        ([("owner_id", 1), ("deck_id", 1)], {}),
        ([("owner_id", 1), ("due_at", 1)], {}),
        ([("deck_id", 1), ("word.normalized", 1)], {"unique": True}),
        ([("deck_id", 1), ("created_at", 1)], {}),
    ]

    # Índices para collection decks
    DECKS_INDEXES = [
        ("owner_id", 1),
        ("title", 1),
        ("created_at", 1),
        ("updated_at", 1),
        ("card_count", 1),
        ([("owner_id", 1), ("category_id", 1)], {}),
    ]

    # Índices para collection categories
    CATEGORIES_INDEXES = [
        ("owner_id", 1),
        ("name", 1),
    ]

    # Índices para collection card_reviews
    CARD_REVIEWS_INDEXES = [
        ("owner_id", 1),
        ("card_id", 1),
        ("reviewed_at", 1),
        ([("owner_id", 1), ("card_id", 1)], {}),
    ]

    # Índices para collection generation_sessions
    SESSIONS_INDEXES = [
        ("deck_id", 1),
        ("status", 1),
        ("created_at", 1),
        ("updated_at", 1),
        ("completed_at", 1),
        ([("deck_id", 1), ("status", 1)], {}),
        ([("deck_id", 1), ("created_at", -1)], {}),
    ]

    @staticmethod
    def get_all_indexes() -> Dict[str, List]:
        """
        Retorna todos os índices organizados por collection.

        Returns:
            Dicionário com índices por collection
        """
        return {
            "cards": IndexDefinitions.CARDS_INDEXES,
            "decks": IndexDefinitions.DECKS_INDEXES,
            "categories": IndexDefinitions.CATEGORIES_INDEXES,
            "card_reviews": IndexDefinitions.CARD_REVIEWS_INDEXES,
            "generation_sessions": IndexDefinitions.SESSIONS_INDEXES
        }
