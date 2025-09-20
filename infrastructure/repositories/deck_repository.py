"""
Implementação MongoDB do DeckRepository

Este módulo implementa a interface IDeckRepository usando MongoDB como
banco de dados. Utiliza Motor para operações assíncronas e implementa
todas as operações definidas na interface.
"""

import uuid
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError, OperationFailure
from bson import ObjectId

from domain.entities.deck import Deck
from domain.repositories.ideck_repository import IDeckRepository
from infrastructure.database.mongodb_connection import ensure_mongodb_connection
from infrastructure.database.schemas import DeckSchema
from infrastructure.repositories.card_repository import RepositoryError


class DeckNotFoundError(RepositoryError):
    """
    Exceção para quando um deck não é encontrado.
    """
    pass


class DeckRepository(IDeckRepository):
    """
    Implementação MongoDB do DeckRepository.
    
    Implementa todas as operações definidas na interface IDeckRepository
    usando MongoDB como banco de dados.
    """
    
    def __init__(self):
        """
        Inicializa o repositório.
        """
        self._collection_name = "decks"
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
    
    async def save(self, deck: Deck) -> Deck:
        """
        Salva um deck no banco de dados.
        
        Args:
            deck: Deck a ser salvo
            
        Returns:
            Deck salvo
            
        Raises:
            RepositoryError: Se houver erro na persistência
        """
        try:
            collection = await self._get_collection()
            deck_data = deck.to_dict()
            document = DeckSchema.to_document(deck_data)
            
            # Insere o documento
            result = await collection.insert_one(document)
            
            # Atualiza o ID do deck com o ObjectId gerado (converte para UUID)
            deck.id = uuid.UUID(str(result.inserted_id))
            
            return deck
            
        except DuplicateKeyError as e:
            raise RepositoryError(f"Deck with duplicate key: {e}")
        except Exception as e:
            raise RepositoryError(f"Failed to save deck: {e}")
    
    async def find_by_id(self, deck_id: uuid.UUID) -> Optional[Deck]:
        """
        Busca um deck pelo ID.
        
        Args:
            deck_id: ID do deck
            
        Returns:
            Deck se encontrado, None caso contrário
            
        Raises:
            RepositoryError: Se houver erro na consulta
        """
        try:
            collection = await self._get_collection()
            document = await collection.find_one({"_id": ObjectId(str(deck_id))})
            
            if document is None:
                return None
            
            deck_data = DeckSchema.from_document(document)
            deck = Deck.from_dict(deck_data)
            
            # Carrega os cards do deck
            from infrastructure.repositories.card_repository import CardRepository
            card_repository = CardRepository()
            cards = await card_repository.find_by_deck_id(deck_id)
            deck.cards = cards
            
            return deck
            
        except Exception as e:
            raise RepositoryError(f"Failed to find deck by ID: {e}")
    
    async def find_by_title(self, title: str) -> List[Deck]:
        """
        Busca decks por título.
        
        Args:
            title: Título para buscar (case insensitive)
            
        Returns:
            Lista de decks com títulos similares
            
        Raises:
            RepositoryError: Se houver erro na consulta
        """
        try:
            collection = await self._get_collection()
            
            # Busca case insensitive
            cursor = collection.find({
                "title": {"$regex": title, "$options": "i"}
            })
            documents = await cursor.to_list(length=None)
            
            decks = []
            for document in documents:
                deck_data = DeckSchema.from_document(document)
                deck = Deck.from_dict(deck_data)
                decks.append(deck)
            
            return decks
            
        except Exception as e:
            raise RepositoryError(f"Failed to find decks by title: {e}")
    
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Deck]:
        """
        Busca todos os decks com paginação.
        
        Args:
            skip: Número de registros para pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de decks
            
        Raises:
            RepositoryError: Se houver erro na consulta
        """
        try:
            collection = await self._get_collection()
            cursor = collection.find().skip(skip).limit(limit).sort("created_at", -1)
            documents = await cursor.to_list(length=None)
            
            decks = []
            for document in documents:
                deck_data = DeckSchema.from_document(document)
                deck = Deck.from_dict(deck_data)
                decks.append(deck)
            
            return decks
            
        except Exception as e:
            raise RepositoryError(f"Failed to find all decks: {e}")
    
    async def find_by_user_id(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Deck]:
        """
        Busca decks de um usuário específico.
        
        Args:
            user_id: ID do usuário
            skip: Número de registros para pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de decks do usuário
            
        Raises:
            RepositoryError: Se houver erro na consulta
        """
        try:
            collection = await self._get_collection()
            
            # Por enquanto, retorna todos os decks
            # Em uma implementação futura, adicionaríamos campo user_id
            cursor = collection.find().skip(skip).limit(limit).sort("created_at", -1)
            documents = await cursor.to_list(length=None)
            
            decks = []
            for document in documents:
                deck_data = DeckSchema.from_document(document)
                deck = Deck.from_dict(deck_data)
                decks.append(deck)
            
            return decks
            
        except Exception as e:
            raise RepositoryError(f"Failed to find decks by user ID: {e}")
    
    async def update(self, deck: Deck) -> Deck:
        """
        Atualiza um deck existente.
        
        Args:
            deck: Deck com dados atualizados
            
        Returns:
            Deck atualizado
            
        Raises:
            RepositoryError: Se houver erro na atualização
            DeckNotFoundError: Se o deck não existir
        """
        try:
            collection = await self._get_collection()
            deck_data = deck.to_dict()
            document = DeckSchema.to_document(deck_data)
            
            # Remove o _id do documento para atualização
            document.pop("_id", None)
            
            result = await collection.replace_one(
                {"_id": ObjectId(str(deck.id))},
                document
            )
            
            if result.matched_count == 0:
                raise DeckNotFoundError(f"Deck with ID {deck.id} not found")
            
            return deck
            
        except DeckNotFoundError:
            raise
        except Exception as e:
            raise RepositoryError(f"Failed to update deck: {e}")
    
    async def delete(self, deck_id: uuid.UUID) -> bool:
        """
        Remove um deck do banco de dados.
        
        Args:
            deck_id: ID do deck a ser removido
            
        Returns:
            True se o deck foi removido, False se não foi encontrado
            
        Raises:
            RepositoryError: Se houver erro na remoção
        """
        try:
            collection = await self._get_collection()
            
            # Remove o deck
            result = await collection.delete_one({"_id": ObjectId(str(deck_id))})
            
            if result.deleted_count > 0:
                # Remove todos os cards do deck
                from infrastructure.repositories.card_repository import CardRepository
                card_repository = CardRepository()
                await card_repository.delete_by_deck_id(deck_id)
                
                # Remove todas as sessões de geração do deck
                from infrastructure.repositories.generation_session_repository import GenerationSessionRepository
                session_repository = GenerationSessionRepository()
                await session_repository.delete_by_deck_id(deck_id)
                
                return True
            
            return False
            
        except Exception as e:
            raise RepositoryError(f"Failed to delete deck: {e}")
    
    async def count(self) -> int:
        """
        Conta o total de decks no banco.
        
        Returns:
            Número total de decks
            
        Raises:
            RepositoryError: Se houver erro na contagem
        """
        try:
            collection = await self._get_collection()
            return await collection.count_documents({})
            
        except Exception as e:
            raise RepositoryError(f"Failed to count decks: {e}")
    
    async def count_by_user_id(self, user_id: str) -> int:
        """
        Conta o número de decks de um usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Número de decks do usuário
            
        Raises:
            RepositoryError: Se houver erro na contagem
        """
        try:
            collection = await self._get_collection()
            
            # Por enquanto, retorna total de decks
            # Em uma implementação futura, filtraria por user_id
            return await collection.count_documents({})
            
        except Exception as e:
            raise RepositoryError(f"Failed to count decks by user ID: {e}")
    
    async def exists(self, deck_id: uuid.UUID) -> bool:
        """
        Verifica se um deck existe.
        
        Args:
            deck_id: ID do deck
            
        Returns:
            True se o deck existe, False caso contrário
            
        Raises:
            RepositoryError: Se houver erro na verificação
        """
        try:
            collection = await self._get_collection()
            count = await collection.count_documents({"_id": ObjectId(str(deck_id))})
            return count > 0
            
        except Exception as e:
            raise RepositoryError(f"Failed to check if deck exists: {e}")
    
    async def exists_by_title(self, title: str, user_id: Optional[str] = None) -> bool:
        """
        Verifica se já existe um deck com o título especificado.
        
        Args:
            title: Título para verificar
            user_id: ID do usuário (opcional, para verificar apenas para um usuário)
            
        Returns:
            True se já existe um deck com esse título
            
        Raises:
            RepositoryError: Se houver erro na verificação
        """
        try:
            collection = await self._get_collection()
            
            query = {"title": {"$regex": f"^{title}$", "$options": "i"}}
            # Em uma implementação futura, adicionaríamos filtro por user_id
            
            count = await collection.count_documents(query)
            return count > 0
            
        except Exception as e:
            raise RepositoryError(f"Failed to check if title exists: {e}")
