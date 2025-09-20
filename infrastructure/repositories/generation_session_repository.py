"""
Implementação MongoDB do GenerationSessionRepository

Este módulo implementa a interface IGenerationSessionRepository usando MongoDB como
banco de dados. Utiliza Motor para operações assíncronas e implementa
todas as operações definidas na interface.
"""

import uuid
from typing import List, Optional
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError, OperationFailure
from bson import ObjectId

from domain.entities.generation_session import GenerationSession, GenerationStatus
from domain.repositories.igeneration_session_repository import IGenerationSessionRepository
from infrastructure.database.mongodb_connection import ensure_mongodb_connection
from infrastructure.database.schemas import GenerationSessionSchema
from infrastructure.repositories.card_repository import RepositoryError


class SessionNotFoundError(RepositoryError):
    """
    Exceção para quando uma sessão não é encontrada.
    """
    pass


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
        self._collection: Optional[AsyncIOMotorCollection] = None
    
    async def _get_collection(self) -> AsyncIOMotorCollection:
        """
        Retorna a collection MongoDB.
        
        Returns:
            Collection MongoDB
            
        Raises:
            RepositoryError: Se não conseguir conectar
        """
        if self._collection is None:
            try:
                mongodb_manager = await ensure_mongodb_connection()
                self._collection = await mongodb_manager.get_collection(self._collection_name)
            except Exception as e:
                raise RepositoryError(f"Failed to get MongoDB collection: {e}")
        
        return self._collection
    
    async def save(self, session: GenerationSession) -> GenerationSession:
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
            collection = await self._get_collection()
            session_data = session.to_dict()
            document = GenerationSessionSchema.to_document(session_data)
            
            # Insere o documento
            result = await collection.insert_one(document)
            
            # Atualiza o ID da sessão com o ObjectId gerado
            session.id = uuid.UUID(str(result.inserted_id))
            
            return session
            
        except DuplicateKeyError as e:
            raise RepositoryError(f"Session with duplicate key: {e}")
        except Exception as e:
            raise RepositoryError(f"Failed to save session: {e}")
    
    async def find_by_id(self, session_id: uuid.UUID) -> Optional[GenerationSession]:
        """
        Busca uma sessão pelo ID.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            Sessão se encontrada, None caso contrário
            
        Raises:
            RepositoryError: Se houver erro na consulta
        """
        try:
            collection = await self._get_collection()
            document = await collection.find_one({"_id": ObjectId(str(session_id))})
            
            if document is None:
                return None
            
            session_data = GenerationSessionSchema.from_document(document)
            session = GenerationSession.from_dict(session_data)
            
            # Carrega os cards gerados da sessão
            from infrastructure.repositories.card_repository import CardRepository
            card_repository = CardRepository()
            cards = await card_repository.find_by_deck_id(session.deck_id)
            session.generated_cards = cards
            
            return session
            
        except Exception as e:
            raise RepositoryError(f"Failed to find session by ID: {e}")
    
    async def find_by_deck_id(self, deck_id: uuid.UUID) -> List[GenerationSession]:
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
            collection = await self._get_collection()
            cursor = collection.find({"deck_id": ObjectId(str(deck_id))}).sort("created_at", -1)
            documents = await cursor.to_list(length=None)
            
            sessions = []
            for document in documents:
                session_data = GenerationSessionSchema.from_document(document)
                session = GenerationSession.from_dict(session_data)
                sessions.append(session)
            
            return sessions
            
        except Exception as e:
            raise RepositoryError(f"Failed to find sessions by deck ID: {e}")
    
    async def find_by_status(self, status: GenerationStatus) -> List[GenerationSession]:
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
            collection = await self._get_collection()
            cursor = collection.find({"status": status.value}).sort("created_at", -1)
            documents = await cursor.to_list(length=None)
            
            sessions = []
            for document in documents:
                session_data = GenerationSessionSchema.from_document(document)
                session = GenerationSession.from_dict(session_data)
                sessions.append(session)
            
            return sessions
            
        except Exception as e:
            raise RepositoryError(f"Failed to find sessions by status: {e}")
    
    async def find_by_context(self, context: str) -> List[GenerationSession]:
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
            collection = await self._get_collection()
            cursor = collection.find({"context": context}).sort("created_at", -1)
            documents = await cursor.to_list(length=None)
            
            sessions = []
            for document in documents:
                session_data = GenerationSessionSchema.from_document(document)
                session = GenerationSession.from_dict(session_data)
                sessions.append(session)
            
            return sessions
            
        except Exception as e:
            raise RepositoryError(f"Failed to find sessions by context: {e}")
    
    async def find_active_sessions(self, deck_id: Optional[uuid.UUID] = None) -> List[GenerationSession]:
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
            collection = await self._get_collection()
            
            active_statuses = [
                GenerationStatus.PENDING.value,
                GenerationStatus.IN_PROGRESS.value
            ]
            
            query = {"status": {"$in": active_statuses}}
            if deck_id:
                query["deck_id"] = ObjectId(str(deck_id))
            
            cursor = collection.find(query).sort("created_at", -1)
            documents = await cursor.to_list(length=None)
            
            sessions = []
            for document in documents:
                session_data = GenerationSessionSchema.from_document(document)
                session = GenerationSession.from_dict(session_data)
                sessions.append(session)
            
            return sessions
            
        except Exception as e:
            raise RepositoryError(f"Failed to find active sessions: {e}")
    
    async def find_finished_sessions(self, deck_id: Optional[uuid.UUID] = None) -> List[GenerationSession]:
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
            collection = await self._get_collection()
            
            finished_statuses = [
                GenerationStatus.COMPLETED.value,
                GenerationStatus.FAILED.value,
                GenerationStatus.CANCELLED.value
            ]
            
            query = {"status": {"$in": finished_statuses}}
            if deck_id:
                query["deck_id"] = ObjectId(str(deck_id))
            
            cursor = collection.find(query).sort("created_at", -1)
            documents = await cursor.to_list(length=None)
            
            sessions = []
            for document in documents:
                session_data = GenerationSessionSchema.from_document(document)
                session = GenerationSession.from_dict(session_data)
                sessions.append(session)
            
            return sessions
            
        except Exception as e:
            raise RepositoryError(f"Failed to find finished sessions: {e}")
    
    async def find_recent_sessions(self, limit: int = 10, deck_id: Optional[uuid.UUID] = None) -> List[GenerationSession]:
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
            collection = await self._get_collection()
            
            query = {}
            if deck_id:
                query["deck_id"] = ObjectId(str(deck_id))
            
            cursor = collection.find(query).sort("created_at", -1).limit(limit)
            documents = await cursor.to_list(length=None)
            
            sessions = []
            for document in documents:
                session_data = GenerationSessionSchema.from_document(document)
                session = GenerationSession.from_dict(session_data)
                sessions.append(session)
            
            return sessions
            
        except Exception as e:
            raise RepositoryError(f"Failed to find recent sessions: {e}")
    
    async def update(self, session: GenerationSession) -> GenerationSession:
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
            collection = await self._get_collection()
            session_data = session.to_dict()
            document = GenerationSessionSchema.to_document(session_data)
            
            # Remove o _id do documento para atualização
            document.pop("_id", None)
            
            result = await collection.replace_one(
                {"_id": ObjectId(str(session.id))},
                document
            )
            
            if result.matched_count == 0:
                raise SessionNotFoundError(f"Session with ID {session.id} not found")
            
            return session
            
        except SessionNotFoundError:
            raise
        except Exception as e:
            raise RepositoryError(f"Failed to update session: {e}")
    
    async def delete(self, session_id: uuid.UUID) -> bool:
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
            collection = await self._get_collection()
            result = await collection.delete_one({"_id": ObjectId(str(session_id))})
            
            return result.deleted_count > 0
            
        except Exception as e:
            raise RepositoryError(f"Failed to delete session: {e}")
    
    async def delete_by_deck_id(self, deck_id: uuid.UUID) -> int:
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
            collection = await self._get_collection()
            result = await collection.delete_many({"deck_id": ObjectId(str(deck_id))})
            
            return result.deleted_count
            
        except Exception as e:
            raise RepositoryError(f"Failed to delete sessions by deck ID: {e}")
    
    async def count(self) -> int:
        """
        Conta o total de sessões no banco.
        
        Returns:
            Número total de sessões
            
        Raises:
            RepositoryError: Se houver erro na contagem
        """
        try:
            collection = await self._get_collection()
            return await collection.count_documents({})
            
        except Exception as e:
            raise RepositoryError(f"Failed to count sessions: {e}")
    
    async def count_by_deck_id(self, deck_id: uuid.UUID) -> int:
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
            collection = await self._get_collection()
            return await collection.count_documents({"deck_id": ObjectId(str(deck_id))})
            
        except Exception as e:
            raise RepositoryError(f"Failed to count sessions by deck ID: {e}")
    
    async def count_by_status(self, status: GenerationStatus) -> int:
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
            collection = await self._get_collection()
            return await collection.count_documents({"status": status.value})
            
        except Exception as e:
            raise RepositoryError(f"Failed to count sessions by status: {e}")
    
    async def exists(self, session_id: uuid.UUID) -> bool:
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
            collection = await self._get_collection()
            count = await collection.count_documents({"_id": ObjectId(str(session_id))})
            return count > 0
            
        except Exception as e:
            raise RepositoryError(f"Failed to check if session exists: {e}")
    
    async def cleanup_old_sessions(self, days_old: int = 30) -> int:
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
            collection = await self._get_collection()
            
            # Calcula data limite
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Remove sessões antigas que estão finalizadas
            result = await collection.delete_many({
                "created_at": {"$lt": cutoff_date},
                "status": {
                    "$in": [
                        GenerationStatus.COMPLETED.value,
                        GenerationStatus.FAILED.value,
                        GenerationStatus.CANCELLED.value
                    ]
                }
            })
            
            return result.deleted_count
            
        except Exception as e:
            raise RepositoryError(f"Failed to cleanup old sessions: {e}")
