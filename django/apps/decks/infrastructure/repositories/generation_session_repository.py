"""
Implementação MongoDB do GenerationSessionRepository

Este módulo implementa a interface IGenerationSessionRepository usando MongoDB
como banco de dados, via pymongo (síncrono). Implementa todas as operações
definidas na interface.
"""

import uuid
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError, OperationFailure
from bson import ObjectId

from apps.decks.domain.entities.generation_session import (
    GenerationSession,
    GenerationStatus,
)
from apps.decks.domain.repositories.igeneration_session_repository import (
    IGenerationSessionRepository,
)
from apps.decks.infrastructure.exceptions import RepositoryError, SessionNotFoundError
from apps.decks.infrastructure.mongodb_connection import ensure_mongodb_connection
from apps.decks.infrastructure.schemas import GenerationSessionSchema, uuid_to_object_id


class GenerationSessionRepository(IGenerationSessionRepository):
    """
    Implementação MongoDB do GenerationSessionRepository.

    Implementa todas as operações definidas na interface IGenerationSessionRepository
    usando MongoDB como banco de dados.
    """

    def __init__(self):
        """
        Inicializa o repositório.
        """
        self._collection_name = "generation_sessions"

    def _get_collection(self) -> Collection:
        """
        Retorna a collection MongoDB.

        Returns:
            Collection MongoDB

        Raises:
            RepositoryError: Se não conseguir conectar
        """
        try:
            mongodb_manager = ensure_mongodb_connection()
            return mongodb_manager.get_collection(self._collection_name)
        except Exception as e:
            raise RepositoryError(f"Failed to get MongoDB collection: {e}")

    def save(self, session: GenerationSession) -> GenerationSession:
        """
        Salva uma sessão de geração no banco de dados.

        Args:
            session: Sessão a ser salva

        Returns:
            Sessão salva

        Raises:
            RepositoryError: Se houver erro na persistência
        """
        try:
            collection = self._get_collection()
            session_data = session.to_dict()
            document = GenerationSessionSchema.to_document(session_data)

            # Insere o documento
            result = collection.insert_one(document)

            # Atualiza o ID da sessão com o ObjectId gerado
            session.id = uuid.UUID(int=int(str(result.inserted_id), 16))

            return session

        except DuplicateKeyError as e:
            raise RepositoryError(f"Session with duplicate key: {e}")
        except Exception as e:
            raise RepositoryError(f"Failed to save session: {e}")

    def find_by_id(
        self, session_id: uuid.UUID, owner_id: str
    ) -> Optional[GenerationSession]:
        """
        Busca uma sessão pelo ID.

        Args:
            session_id: ID da sessão
            owner_id: dono dos cards do deck associado (ver docstring na
                interface, IGenerationSessionRepository)

        Returns:
            Sessão se encontrada, None caso contrário

        Raises:
            RepositoryError: Se houver erro na consulta
        """
        try:
            collection = self._get_collection()
            document = collection.find_one({"_id": uuid_to_object_id(session_id)})

            if document is None:
                return None

            session_data = GenerationSessionSchema.from_document(document)
            session = GenerationSession.from_dict(session_data)

            # Carrega os cards gerados da sessão
            from apps.decks.infrastructure.repositories.card_repository import (
                CardRepository,
            )

            card_repository = CardRepository()
            cards = card_repository.find_by_deck_id(session.deck_id, owner_id)
            session.generated_cards = cards

            return session

        except Exception as e:
            raise RepositoryError(f"Failed to find session by ID: {e}")

    def find_by_deck_id(self, deck_id: uuid.UUID) -> List[GenerationSession]:
        """
        Busca todas as sessões de um deck.

        Args:
            deck_id: ID do deck

        Returns:
            Lista de sessões do deck

        Raises:
            RepositoryError: Se houver erro na consulta
        """
        try:
            collection = self._get_collection()
            cursor = collection.find({"deck_id": uuid_to_object_id(deck_id)}).sort(
                "created_at", -1
            )
            documents = list(cursor)

            sessions = []
            for document in documents:
                session_data = GenerationSessionSchema.from_document(document)
                session = GenerationSession.from_dict(session_data)
                sessions.append(session)

            return sessions

        except Exception as e:
            raise RepositoryError(f"Failed to find sessions by deck ID: {e}")

    def find_by_status(self, status: GenerationStatus) -> List[GenerationSession]:
        """
        Busca sessões por status.

        Args:
            status: Status das sessões

        Returns:
            Lista de sessões com o status especificado

        Raises:
            RepositoryError: Se houver erro na consulta
        """
        try:
            collection = self._get_collection()
            cursor = collection.find({"status": status.value}).sort("created_at", -1)
            documents = list(cursor)

            sessions = []
            for document in documents:
                session_data = GenerationSessionSchema.from_document(document)
                session = GenerationSession.from_dict(session_data)
                sessions.append(session)

            return sessions

        except Exception as e:
            raise RepositoryError(f"Failed to find sessions by status: {e}")

    def find_by_context(self, context: str) -> List[GenerationSession]:
        """
        Busca sessões por contexto.

        Args:
            context: Contexto para buscar

        Returns:
            Lista de sessões que usam o contexto

        Raises:
            RepositoryError: Se houver erro na consulta
        """
        try:
            collection = self._get_collection()
            cursor = collection.find({"context": context}).sort("created_at", -1)
            documents = list(cursor)

            sessions = []
            for document in documents:
                session_data = GenerationSessionSchema.from_document(document)
                session = GenerationSession.from_dict(session_data)
                sessions.append(session)

            return sessions

        except Exception as e:
            raise RepositoryError(f"Failed to find sessions by context: {e}")

    def find_active_sessions(
        self, deck_id: Optional[uuid.UUID] = None
    ) -> List[GenerationSession]:
        """
        Busca sessões ativas (não finalizadas).

        Args:
            deck_id: ID do deck (opcional, para filtrar por deck)

        Returns:
            Lista de sessões ativas

        Raises:
            RepositoryError: Se houver erro na consulta
        """
        try:
            collection = self._get_collection()

            active_statuses = [
                GenerationStatus.PENDING.value,
                GenerationStatus.IN_PROGRESS.value,
            ]

            query = {"status": {"$in": active_statuses}}
            if deck_id:
                query["deck_id"] = uuid_to_object_id(deck_id)

            cursor = collection.find(query).sort("created_at", -1)
            documents = list(cursor)

            sessions = []
            for document in documents:
                session_data = GenerationSessionSchema.from_document(document)
                session = GenerationSession.from_dict(session_data)
                sessions.append(session)

            return sessions

        except Exception as e:
            raise RepositoryError(f"Failed to find active sessions: {e}")

    def find_finished_sessions(
        self, deck_id: Optional[uuid.UUID] = None
    ) -> List[GenerationSession]:
        """
        Busca sessões finalizadas (concluídas, falhadas ou canceladas).

        Args:
            deck_id: ID do deck (opcional, para filtrar por deck)

        Returns:
            Lista de sessões finalizadas

        Raises:
            RepositoryError: Se houver erro na consulta
        """
        try:
            collection = self._get_collection()

            finished_statuses = [
                GenerationStatus.COMPLETED.value,
                GenerationStatus.FAILED.value,
                GenerationStatus.CANCELLED.value,
            ]

            query = {"status": {"$in": finished_statuses}}
            if deck_id:
                query["deck_id"] = uuid_to_object_id(deck_id)

            cursor = collection.find(query).sort("created_at", -1)
            documents = list(cursor)

            sessions = []
            for document in documents:
                session_data = GenerationSessionSchema.from_document(document)
                session = GenerationSession.from_dict(session_data)
                sessions.append(session)

            return sessions

        except Exception as e:
            raise RepositoryError(f"Failed to find finished sessions: {e}")

    def find_recent_sessions(
        self, limit: int = 10, deck_id: Optional[uuid.UUID] = None
    ) -> List[GenerationSession]:
        """
        Busca as sessões mais recentes.

        Args:
            limit: Número máximo de sessões a retornar
            deck_id: ID do deck (opcional, para filtrar por deck)

        Returns:
            Lista de sessões ordenadas por data de criação (mais recentes primeiro)

        Raises:
            RepositoryError: Se houver erro na consulta
        """
        try:
            collection = self._get_collection()

            query = {}
            if deck_id:
                query["deck_id"] = uuid_to_object_id(deck_id)

            cursor = collection.find(query).sort("created_at", -1).limit(limit)
            documents = list(cursor)

            sessions = []
            for document in documents:
                session_data = GenerationSessionSchema.from_document(document)
                session = GenerationSession.from_dict(session_data)
                sessions.append(session)

            return sessions

        except Exception as e:
            raise RepositoryError(f"Failed to find recent sessions: {e}")

    def update(self, session: GenerationSession) -> GenerationSession:
        """
        Atualiza uma sessão existente.

        Args:
            session: Sessão com dados atualizados

        Returns:
            Sessão atualizada

        Raises:
            RepositoryError: Se houver erro na atualização
            SessionNotFoundError: Se a sessão não existir
        """
        try:
            collection = self._get_collection()
            session_data = session.to_dict()
            document = GenerationSessionSchema.to_document(session_data)

            # Remove o _id do documento para atualização
            document.pop("_id", None)

            result = collection.replace_one(
                {"_id": uuid_to_object_id(session.id)}, document
            )

            if result.matched_count == 0:
                raise SessionNotFoundError(f"Session with ID {session.id} not found")

            return session

        except SessionNotFoundError:
            raise
        except Exception as e:
            raise RepositoryError(f"Failed to update session: {e}")

    def delete(self, session_id: uuid.UUID) -> bool:
        """
        Remove uma sessão do banco de dados.

        Args:
            session_id: ID da sessão a ser removida

        Returns:
            True se a sessão foi removida, False se não foi encontrada

        Raises:
            RepositoryError: Se houver erro na remoção
        """
        try:
            collection = self._get_collection()
            result = collection.delete_one({"_id": uuid_to_object_id(session_id)})

            return result.deleted_count > 0

        except Exception as e:
            raise RepositoryError(f"Failed to delete session: {e}")

    def delete_by_deck_id(self, deck_id: uuid.UUID) -> int:
        """
        Remove todas as sessões de um deck.

        Args:
            deck_id: ID do deck

        Returns:
            Número de sessões removidas

        Raises:
            RepositoryError: Se houver erro na remoção
        """
        try:
            collection = self._get_collection()
            result = collection.delete_many({"deck_id": uuid_to_object_id(deck_id)})

            return result.deleted_count

        except Exception as e:
            raise RepositoryError(f"Failed to delete sessions by deck ID: {e}")

    def count(self) -> int:
        """
        Conta o total de sessões no banco.

        Returns:
            Número total de sessões

        Raises:
            RepositoryError: Se houver erro na contagem
        """
        try:
            collection = self._get_collection()
            return collection.count_documents({})

        except Exception as e:
            raise RepositoryError(f"Failed to count sessions: {e}")

    def count_by_deck_id(self, deck_id: uuid.UUID) -> int:
        """
        Conta o número de sessões de um deck.

        Args:
            deck_id: ID do deck

        Returns:
            Número de sessões do deck

        Raises:
            RepositoryError: Se houver erro na contagem
        """
        try:
            collection = self._get_collection()
            return collection.count_documents({"deck_id": uuid_to_object_id(deck_id)})

        except Exception as e:
            raise RepositoryError(f"Failed to count sessions by deck ID: {e}")

    def count_by_status(self, status: GenerationStatus) -> int:
        """
        Conta o número de sessões com um status específico.

        Args:
            status: Status das sessões

        Returns:
            Número de sessões com o status

        Raises:
            RepositoryError: Se houver erro na contagem
        """
        try:
            collection = self._get_collection()
            return collection.count_documents({"status": status.value})

        except Exception as e:
            raise RepositoryError(f"Failed to count sessions by status: {e}")

    def exists(self, session_id: uuid.UUID) -> bool:
        """
        Verifica se uma sessão existe.

        Args:
            session_id: ID da sessão

        Returns:
            True se a sessão existe, False caso contrário

        Raises:
            RepositoryError: Se houver erro na verificação
        """
        try:
            collection = self._get_collection()
            count = collection.count_documents({"_id": uuid_to_object_id(session_id)})
            return count > 0

        except Exception as e:
            raise RepositoryError(f"Failed to check if session exists: {e}")

    def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """
        Remove sessões antigas (para limpeza de dados).

        Args:
            days_old: Número de dias para considerar uma sessão como antiga

        Returns:
            Número de sessões removidas

        Raises:
            RepositoryError: Se houver erro na limpeza
        """
        try:
            collection = self._get_collection()

            # Calcula data limite
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)

            # Remove sessões antigas que estão finalizadas
            result = collection.delete_many(
                {
                    "created_at": {"$lt": cutoff_date},
                    "status": {
                        "$in": [
                            GenerationStatus.COMPLETED.value,
                            GenerationStatus.FAILED.value,
                            GenerationStatus.CANCELLED.value,
                        ]
                    },
                }
            )

            return result.deleted_count

        except Exception as e:
            raise RepositoryError(f"Failed to cleanup old sessions: {e}")
